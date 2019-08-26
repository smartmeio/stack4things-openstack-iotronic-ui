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

from iotronic_ui.iot.devices import forms as project_forms
from iotronic_ui.iot.devices import tables as project_tables
from iotronic_ui.iot.devices import tabs as project_tabs


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.DevicesTable
    template_name = 'iot/devices/index.html'
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
        # LOG.debug('DEVICES: %s', devices)
        return devices


class CreateView(forms.ModalFormView):
    template_name = 'iot/devices/create.html'
    modal_header = _("Create Device")
    form_id = "create_device_form"
    form_class = project_forms.CreateDeviceForm
    submit_label = _("Create Device")
    submit_url = reverse_lazy("horizon:iot:devices:create")
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Create Device")


class UpdateView(forms.ModalFormView):
    template_name = 'iot/devices/update.html'
    modal_header = _("Update Device")
    form_id = "update_device_form"
    form_class = project_forms.UpdateDeviceForm
    submit_label = _("Update Device")
    submit_url = "horizon:iot:devices:update"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Update Device")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()
        location = device.location[0]

        return {'uuid': device.uuid,
                'name': device.name,
                'mobile': device.mobile,
                'owner': device.owner,
                'fleet_id': device.fleet,
                'latitude': location["latitude"],
                'longitude': location["longitude"],
                'altitude': location["altitude"]}


class AttachPortView(forms.ModalFormView):
    template_name = 'iot/devices/attachport.html'
    modal_header = _("Attach")
    form_id = "attach_deviceport_form"
    form_class = project_forms.AttachPortForm
    submit_label = _("Attach")
    # submit_url = reverse_lazy("horizon:iot:devices:attachport")
    submit_url = "horizon:iot:devices:attachport"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Attach port")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(AttachPortView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate networks
        networks = api.neutron.network_list(self.request)
        net_choices = []

        networks.sort(key=lambda b: b.name)
        for net in networks:
            for subnet in net["subnets"]:
                net_choices.append((net["id"] + ':' + subnet["id"],
                                   _(net["name"] + ':' + subnet["name"])))

        return {'uuid': device.uuid,
                'name': device.name,
                'networks_list': net_choices}


class DetachPortView(forms.ModalFormView):
    template_name = 'iot/devices/detachport.html'
    modal_header = _("Detach")
    form_id = "detach_deviceport_form"
    form_class = project_forms.DetachPortForm
    submit_label = _("Detach")
    # submit_url = reverse_lazy("horizon:iot:devices:detachport")
    submit_url = "horizon:iot:devices:detachport"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Detach port")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(DetachPortView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        ports = api.iotronic.port_list(self.request, device.uuid)

        # TO BE REMOVED (change it once the port_list per device is
        # completed and tested !
        # ################################################################
        # LOG.debug("PORTS: %s", ports)

        ports.sort(key=lambda b: b.name)
        filtered_ports = []
        for port in ports:
            if port._info["board_uuid"] == device.uuid:
                filtered_ports.append((port._info["uuid"],
                                      _(port._info["ip"])))

        ports = filtered_ports
        # ################################################################

        # Populate device ports
        return {'uuid': device.uuid,
                'name': device.name,
                'ports': ports}


class ActionView(forms.ModalFormView):
    template_name = 'iot/devices/action.html'
    modal_header = _("Action on Device")
    form_id = "action_device_form"
    form_class = project_forms.ActionDeviceForm
    submit_label = _("Action")
    # submit_url = reverse_lazy("horizon:iot:devices:action")
    submit_url = "horizon:iot:devices:action"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Action on Device")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ActionView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate actions (TO BE REPLACED with an action list api)
        actions = ["DeviceNetConfig", "DevicePing", "DeviceEcho",
                   "DeviceUpgradeLR", "DevicePkgOperation",
                   "DeviceRestartLR", "DeviceReboot"]
        actions.sort()

        action_list = []
        for action in actions:
            name = action.replace("Device", "")
            action_list.append((action, _(name)))

        return {'uuid': device.uuid,
                'name': device.name,
                'action_list': action_list}


class PackageActionView(forms.ModalFormView):
    template_name = 'iot/devices/packageaction.html'
    modal_header = _("Action on packages on Device")
    form_id = "package_action_device_form"
    form_class = project_forms.PackageActionDeviceForm
    submit_label = _("Package Action")
    # submit_url = reverse_lazy("horizon:iot:devices:packageaction")
    submit_url = "horizon:iot:devices:packageaction"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Action on packages on Device")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(PackageActionView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        managers = ["apt", "npm", "pip", "pip3"]
        commands = ["install", "remove", "uninstall"]
        managers.sort()
        commands.sort()

        manager_list = []
        command_list = []

        for manager in managers: manager_list.append((manager, _(manager)))
        for command in commands: command_list.append((command, _(command)))

        return {'uuid': device.uuid,
                'name': device.name,
                'manager_list': manager_list,
                'command_list': command_list}


class UpgradeLRView(forms.ModalFormView):
    template_name = 'iot/devices/upgradelr.html'
    modal_header = _("Upgrade LR on Device")
    form_id = "upgrade_lr_form"
    form_class = project_forms.UpgradeLRForm
    submit_label = _("Upgrade")
    # submit_url = reverse_lazy("horizon:iot:devices:upgradelr")
    submit_url = "horizon:iot:devices:upgradelr"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Upgrade LR")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(UpgradeLRView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        return {'uuid': device.uuid,
                'name': device.name}


class RestartLRView(forms.ModalFormView):
    template_name = 'iot/devices/restartlr.html'
    modal_header = _("Restart LR on Device")
    form_id = "restart_lr_form"
    form_class = project_forms.RestartLRForm
    submit_label = _("Restart")
    # submit_url = reverse_lazy("horizon:iot:devices:restartlr")
    submit_url = "horizon:iot:devices:restartlr"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Restart LR")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(RestartLRView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        return {'uuid': device.uuid,
                'name': device.name}


class RebootView(forms.ModalFormView):
    template_name = 'iot/devices/reboot.html'
    modal_header = _("Reboot the Device")
    form_id = "reboot_form"
    form_class = project_forms.RebootForm
    submit_label = _("Reboot")
    # submit_url = reverse_lazy("horizon:iot:devices:reboot")
    submit_url = "horizon:iot:devices:reboot"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Reboot Device")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(RebootView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        return {'uuid': device.uuid,
                'name': device.name}


class NetConfView(forms.ModalFormView):
    template_name = 'iot/devices/netconf.html'
    modal_header = _("Device connections")
    form_id = "netconf_form"
    form_class = project_forms.NetConfForm
    submit_label = _("Show")
    # submit_url = reverse_lazy("horizon:iot:devices:netconf")
    submit_url = "horizon:iot:devices:netconf"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Device connections")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(NetConfView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        return {'uuid': device.uuid,
                'name': device.name}


class PingView(forms.ModalFormView):
    template_name = 'iot/devices/ping.html'
    modal_header = _("Ping")
    form_id = "ping_form"
    form_class = project_forms.PingForm
    submit_label = _("Submit")
    # submit_url = reverse_lazy("horizon:iot:devices:ping")
    submit_url = "horizon:iot:devices:ping"
    success_url = reverse_lazy('horizon:iot:devices:index')
    page_title = _("Ping")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)
        except Exception:
            redirect = reverse("horizon:iot:devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(PingView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        return {'uuid': device.uuid,
                'name': device.name}


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
        table = project_tables.BoardsTable(self.request)
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
            device._info.update(dict(plugins=device_plugins))

            device_webservices = api.iotronic.webservices_on_device(self.request,
                                                                    device_id)

            # LOG.debug('DEVICE %s, WEB SERVICES: %s', device_id, device_webservices)
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

            # LOG.debug("DEVICE: %s\n\n%s", device, device._info)

        except Exception:
            msg = ('Unable to retrieve device %s information') % {'name':
                                                                  device.name}
            exceptions.handle(self.request, msg, ignore=True)
        return device

    def get_tabs(self, request, *args, **kwargs):
        device = self.get_data()
        return self.tab_group_class(request, device=device, **kwargs)


class DeviceDetailView(DetailView):
    redirect_url = 'horizon:iot:devices:index'

    def _get_actions(self, device):
        table = project_tables.DevicesTable(self.request)
        return table.render_row_actions(device)
