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

from django import template
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
# from iotronic_ui import api

LOG = logging.getLogger(__name__)


class DeviceFilterAction(tables.FilterAction):

    # If uncommented it will appear the select menu list of fields
    # and filter button
    """
    filter_type = "server"
    filter_choices = (("name", _("Device Name ="), True),
                      ("type", _("Type ="), True),
                      ("status", _("Status ="), True))
    """

    def filter(self, table, devices, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [device for device in devices
                if q in device.name.lower()]


def show_services(device_info):
    template_name = 'iot/plugins_devices/_cell_services.html'
    context = device_info._info
    # LOG.debug("CONTEXT: %s", context)
    return template.loader.render_to_string(template_name,
                                            context)


class InjectPluginLink(tables.LinkAction):
    name = "inject"
    verbose_name = _("Inject Plugin")
    url = "horizon:iot:plugins_devices:inject"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:inject_plugin"),)


class CallPluginLink(tables.LinkAction):
    name = "call"
    verbose_name = _("Call Plugin")
    url = "horizon:iot:plugins_devices:call"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:call_plugin"),)


class StartPluginLink(tables.LinkAction):
    name = "start"
    verbose_name = _("Start Plugin")
    url = "horizon:iot:plugins_devices:start"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:start_plugin"),)


class StopPluginLink(tables.LinkAction):
    name = "stop"
    verbose_name = _("Stop Plugin")
    url = "horizon:iot:plugins_devices:stop"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:stop_plugin"),)


class RemovePluginsLink(tables.LinkAction):
    name = "removeplugins"
    verbose_name = _("Remove Plugin(s)")
    url = "horizon:iot:plugins_devices:removeplugins"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:remove_plugins"),)


class DevicesTable(tables.DataTable):
    name = tables.WrappingColumn('name',
                                 link="horizon:iot:plugins_devices:detail",
                                 verbose_name=_('Device Name'))
    type = tables.Column('type', verbose_name=_('Type'))
    # mobile = tables.Column('mobile', verbose_name=_('Mobile'))
    lr_version = tables.Column('lr_version', verbose_name=_('LR version'))
    # fleet = tables.Column('fleet', verbose_name=_('Fleet ID'))
    fleet_name = tables.Column('fleet_name', verbose_name=_('Fleet Name'))
    # code = tables.Column('code', verbose_name=_('Code'))
    status = tables.Column('status', verbose_name=_('Status'))
    uuid = tables.Column('uuid', verbose_name=_('Device ID'))
    # location = tables.Column('location', verbose_name=_('Geo'))
    services = tables.Column(show_services, verbose_name=_('SSH Access'))
    # extra = tables.Column('extra', verbose_name=_('Extra'))

    # Overriding get_object_id method because in IoT service the "id" is
    # identified by the field UUID
    def get_object_id(self, datum):
        return datum.uuid

    class Meta(object):
        name = "devices"
        verbose_name = _("devices")
        row_actions = (InjectPluginLink, CallPluginLink, StartPluginLink,
                       StopPluginLink, RemovePluginsLink,)
        table_actions = (DeviceFilterAction,) 
