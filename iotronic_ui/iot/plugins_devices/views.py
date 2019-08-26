# Copyright 2017-2019 MDSLAB - University of Messina All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

author = "Carmelo Romeo <carmelo.romeo85@gmail.com>"

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
# from horizon import messages
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
# from iotronic_ui.api import iotronic
from openstack_dashboard import policy

from iotronic_ui.iot.plugins_devices import forms as project_forms
from iotronic_ui.iot.plugins_devices import tables as project_tables
from iotronic_ui.iot.plugins_devices import tabs as project_tabs


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.DevicesTable
    template_name = 'iot/plugins_devices/index.html'
    page_title = _("Devices")

    def get_data(self):
        devices = []

        # Admin
        if policy.check((("iot", "iot:list_all_boards"),), self.request):
            try:
                devices = api.iotronic.device_list(self.request, None, None)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve devices list.'))

        # Admin_iot_project
        elif policy.check((("iot", "iot:list_project_boards"),), self.request):
            try:
                devices = api.iotronic.device_list(self.request, None, None)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user devices list.'))

        # Other users
        else:
            try:
                devices = api.iotronic.device_list(self.request, None, None)

            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve user devices list.'))

        for device in devices:
            device_services = api.iotronic.services_on_device(self.request,
                                                              device.uuid,
                                                              True)

            # x = api.iotronic.device_get(self.request, device.uuid, None)
            # LOG.debug('DEVICE: %s', x)
            # TO BE REMOVED
            # ------------------------------------------------------------
            filter_ws = []
            for service in device_services:
                # We are filtering the services that starts with "webservice"
                """
                if ((service["name"] != "webservice") and 
                   (service["name"] != "webservice_ssl")):
                    filter_ws.append(service)
                """
                # We want to show only the "ssh" service
                if (service["name"] == "ssh"):
                    service["wstun_ip"] = device.wstun_ip
                    filter_ws.append(service)

            device_services = filter_ws
            # ------------------------------------------------------------

            # device.__dict__.update(dict(services=device_services))
            device._info.update(dict(services=device_services))

            if device.fleet != None:
                fleet_info = api.iotronic.fleet_get(self.request,
                                                    device.fleet,
                                                    None)

                device.fleet_name = fleet_info.name
            else:
                device.fleet_name = None

        devices.sort(key=lambda b: b.name)
        return devices


class DetailView(tabs.TabView):
    tab_group_class = project_tabs.DeviceDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ device.name|default:device.uuid }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        device = self.get_data()
        context["device"] = device
        context["url"] = reverse(self.redirect_url)
        context["actions"] = self._get_actions(device)

        return context

    def _get_actions(self, device):
        table = project_tables.DevicesTable(self.request)
        return table.render_row_actions(device)

    @memoized.memoized_method
    def get_data(self):

        device = []

        device_id = self.kwargs['device_id']
        try:

            device_ports = []

            device = api.iotronic.device_get(self.request, device_id, None)

            # FIX this problem with the new APIs
            # (remove the "if" clause with a better approach)
            # #################################################################
            ports = api.iotronic.port_list(self.request, device_id)

            for port in ports:
                if port._info["board_uuid"] == device_id:
                    device_ports.append(port._info)
            device._info.update(dict(ports=device_ports))
            # #################################################################

            device_services = api.iotronic.services_on_device(self.request,
                                                              device_id, True)

            # We have to add the wstun_ip to the service
            for service in device_services:
                service["wstun_ip"] = device.wstun_ip

            device._info.update(dict(services=device_services))

            device_plugins = api.iotronic.plugins_on_device(self.request,
                                                            device_id)

            # Create a list with name and uuid
            p_list = []
            for p in device_plugins:
                p_list.append({"uuid": p._info["uuid"], "name": p.name})
            device_plugins = p_list

            device._info.update(dict(plugins=device_plugins))

            device_webservices = api.iotronic.webservices_on_device(self.request,
                                                                    device_id)

            device._info.update(dict(webservices=device_webservices))

            # Adding fleet name
            if device.fleet != None:
                fleet_info = api.iotronic.fleet_get(self.request,
                                                    device.fleet,
                                                    None)

                device.fleet_name = fleet_info.name
            else:
                device.fleet_name = None

            # Adding LR web service description
            lr_ws = api.iotronic.webservice_get_enabled_info(self.request,
                                                             device_id)
            device._info.update(dict(lr_webservice=lr_ws))

        except Exception:
            msg = ('Unable to retrieve device %s information') % {'name':
                                                                  device.name}
            exceptions.handle(self.request, msg, ignore=True)
        return device

    def get_tabs(self, request, *args, **kwargs):
        device = self.get_data()
        return self.tab_group_class(request, device=device, **kwargs)


class DeviceDetailView(DetailView):
    redirect_url = 'horizon:iot:plugins_devices:index'

    def _get_actions(self, device):
        table = project_tables.DevicesTable(self.request)
        return table.render_row_actions(device)


class InjectView(forms.ModalFormView):
    template_name = 'iot/plugins_devices/inject.html'
    modal_header = _("Inject Plugin")
    form_id = "inject_plugin_form"
    form_class = project_forms.InjectPluginForm
    submit_label = _("Inject Plugin")
    # submit_url = reverse_lazy("horizon:iot:plugins_devices:inject")
    submit_url = "horizon:iot:plugins_devices:inject"
    success_url = reverse_lazy('horizon:iot:plugins_devices:index')
    page_title = _("Inject Plugin")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:plugins_devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(InjectView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate plugins (not yet injected)
        plugins = api.iotronic.plugin_list(self.request, None, None,
                                           all_plugins=True)

        plg_ondevice = api.iotronic.plugins_on_device(self.request,
                                                      device.uuid)

        diff = []
        if len(plg_ondevice) != 0:
            for p in plugins:
                count = 0
                for d in plg_ondevice:
                    if d._info["uuid"] == p.uuid:
                        break
                    elif d._info["uuid"] != p.uuid and count == len(plg_ondevice) - 1:
                        diff.append(p)
                    else:
                        count += 1 
            plugins = diff

        plugins.sort(key=lambda b: b.name)

        plugin_list = []
        for plugin in plugins:
            plugin_list.append((plugin.uuid, _(plugin.name)))

        return {'uuid': device.uuid,
                'name': device.name,
                'plugin_list': plugin_list}


class CallView(forms.ModalFormView):
    template_name = 'iot/plugins_devices/call.html'
    modal_header = _("Call Plugin")
    form_id = "call_plugin_form"
    form_class = project_forms.CallPluginForm
    submit_label = _("Call Plugin")
    # submit_url = reverse_lazy("horizon:iot:plugins_devices:call")
    submit_url = "horizon:iot:plugins_devices:call"
    success_url = reverse_lazy('horizon:iot:plugins_devices:index')
    page_title = _("Call Plugin")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:plugins_devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(CallView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate plugins
        plugins = api.iotronic.plugin_list(self.request, None, None,
                                           all_plugins=True)
        plugins.sort(key=lambda b: b.name)

        plugin_list = []
        for plugin in plugins:
            if plugin.callable == True:
                plugin_list.append((plugin.uuid, _(plugin.name)))

        return {'uuid': device.uuid,
                'name': device.name,
                'plugin_list': plugin_list}


class StartView(forms.ModalFormView):
    template_name = 'iot/plugins_devices/start.html'
    modal_header = _("Start Plugin")
    form_id = "call_plugin_form"
    form_class = project_forms.StartPluginForm
    submit_label = _("Start Plugin")
    # submit_url = reverse_lazy("horizon:iot:plugins_devices:start")
    submit_url = "horizon:iot:plugins_devices:start"
    success_url = reverse_lazy('horizon:iot:plugins_devices:index')
    page_title = _("Start Plugin")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:plugins_devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(StartView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate plugins
        # plugins = api.iotronic.plugin_list(self.request, None, None,
        #                                    all_plugins=True)
        plugins = api.iotronic.plugins_on_device(self.request, device.uuid)
        plugins.sort(key=lambda b: b.name)

        plugin_list = []
        for plugin in plugins:
            if plugin.callable == False:
                plugin_list.append((plugin._info["uuid"], _(plugin.name)))

        return {'uuid': device.uuid,
                'name': device.name,
                'plugin_list': plugin_list}


class StopView(forms.ModalFormView):
    template_name = 'iot/plugins_devices/stop.html'
    modal_header = _("Stop Plugin")
    form_id = "call_plugin_form"
    form_class = project_forms.StopPluginForm
    submit_label = _("Stop Plugin")
    # submit_url = reverse_lazy("horizon:iot:plugins_devices:stop")
    submit_url = "horizon:iot:plugins_devices:stop"
    success_url = reverse_lazy('horizon:iot:plugins_devices:index')
    page_title = _("Stop Plugin")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:plugins_devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(StopView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate plugins
        plugins = api.iotronic.plugin_list(self.request, None, None,
                                           all_plugins=True)
        plugins.sort(key=lambda b: b.name)

        plugin_list = []
        for plugin in plugins:
            if plugin.callable == False:
                plugin_list.append((plugin.uuid, _(plugin.name)))

        return {'uuid': device.uuid,
                'name': device.name,
                'plugin_list': plugin_list}


class RemovePluginsView(forms.ModalFormView):
    template_name = 'iot/plugins_devices/removeplugins.html'
    modal_header = _("Remove Plugins from device")
    form_id = "remove_deviceplugins_form"
    form_class = project_forms.RemovePluginsForm
    submit_label = _("Remove")
    # submit_url = reverse_lazy("horizon:iot:plugins_devices:removeplugins")
    submit_url = "horizon:iot:plugins_devices:removeplugins"
    success_url = reverse_lazy('horizon:iot:plugins_devices:index')
    page_title = _("Remove Plugins from device")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:plugins_devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(RemovePluginsView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate plugins
        # TO BE DONE.....filter by available on this device!!!
        # plugins = api.iotronic.plugin_list(self.request, None, None)
        plugins = api.iotronic.plugins_on_device(self.request, device.uuid)
        plugins.sort(key=lambda b: b.name)

        plugin_list = []
        for plugin in plugins:
            plugin_list.append((plugin._info["uuid"], _(plugin.name)))

        return {'uuid': device.uuid,
                'name': device.name,
                'plugin_list': plugin_list}
