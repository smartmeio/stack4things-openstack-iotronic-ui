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

from iotronic_ui.iot.webservices_devices import forms as project_forms
from iotronic_ui.iot.webservices_devices import tables as project_tables
from iotronic_ui.iot.webservices_devices import tabs as project_tabs


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = project_tables.DevicesTable
    template_name = 'iot/webservices_devices/index.html'
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


class EnableWebServiceView(forms.ModalFormView):
    template_name = 'iot/webservices_devices/enablewebservice.html'
    modal_header = _("Enable Web Services Manager")
    form_id = "webservice_enable_form"
    form_class = project_forms.EnableWebServiceForm
    submit_label = _("Enable")
    # submit_url = reverse_lazy("horizon:iot:webservices_devices:enablewebservice")
    submit_url = "horizon:iot:webservices_devices:enablewebservice"
    success_url = reverse_lazy('horizon:iot:webservices_devices:index')
    page_title = _("Enable")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)

        except Exception:
            redirect = reverse("horizon:iot:webservices_devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(EnableWebServiceView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        # Populate zones
        zones = sorted(getattr(settings, 'IOTRONIC_ZONES'))
        zone_choices = []

        for zone in zones:
            zone_choices.append((zone, _(zone)))
            # LOG.debug('ZONE: %s', zone)

        return {'uuid': device.uuid,
                'name': device.name,
                'zones_list': zone_choices}


class DisableWebServiceView(forms.ModalFormView):
    template_name = 'iot/webservices_devices/disablewebservice.html'
    modal_header = _("Disable Web Services Manager")
    form_id = "webservice_disable_form"
    form_class = project_forms.DisableWebServiceForm
    submit_label = _("Disable")
    # submit_url = reverse_lazy("horizon:iot:webservices_devices:disablewebservice")
    submit_url = "horizon:iot:webservices_devices:disablewebservice"
    success_url = reverse_lazy('horizon:iot:webservices_devices:index')
    page_title = _("Disable")

    @memoized.memoized_method
    def get_object(self):
        try:
            return api.iotronic.device_get(self.request,
                                           self.kwargs['device_id'],
                                           None)

        except Exception:
            redirect = reverse("horizon:iot:webservices_devices:index")
            exceptions.handle(self.request,
                              _('Unable to get device information.'),
                              redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(DisableWebServiceView, self).get_context_data(**kwargs)
        args = (self.get_object().uuid,)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

    def get_initial(self):
        device = self.get_object()

        return {'uuid': device.uuid,
                'name': device.name}


class DeviceDetailView(DetailView):
    redirect_url = 'horizon:iot:webservices_devices:index'

    def _get_actions(self, device):
        table = project_tables.DevicesTable(self.request)
        return table.render_row_actions(device)
