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


class CreateDeviceLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Device")
    url = "horizon:iot:devices:create"
    classes = ("ajax-modal",)
    icon = "plus"
    # policy_rules = (("iot", "iot:create_device"),)


class EditDeviceLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = "horizon:iot:devices:update"
    classes = ("ajax-modal",)
    icon = "pencil"
    # policy_rules = (("iot", "iot:update_device"),)


class AttachPortLink(tables.LinkAction):
    name = "attachport"
    verbose_name = _("Attach Port")
    url = "horizon:iot:devices:attachport"
    classes = ("ajax-modal",)
    icon = "plus"


class DetachPortLink(tables.LinkAction):
    name = "detachport"
    verbose_name = _("Detach Port")
    url = "horizon:iot:devices:detachport"
    classes = ("ajax-modal",)
    icon = "plus"


class ActionLink(tables.LinkAction):
    name = "action"
    verbose_name = _("Action")
    url = "horizon:iot:devices:action"
    classes = ("ajax-modal",)
    icon = "plus"


class PackageActionLink(tables.LinkAction):
    name = "packageaction"
    verbose_name = _("Package Action")
    url = "horizon:iot:devices:packageaction"
    classes = ("ajax-modal",)
    icon = "plus"


class UpgradeLRLink(tables.LinkAction):
    name = "upgradelr"
    verbose_name = _("Upgrade LR")
    url = "horizon:iot:devices:upgradelr"
    classes = ("ajax-modal",)
    icon = "plus"


class RestartLRLink(tables.LinkAction):
    name = "restartlr"
    verbose_name = _("Restart LR")
    url = "horizon:iot:devices:restartlr"
    classes = ("ajax-modal",)
    icon = "plus"


class RebootLink(tables.LinkAction):
    name = "reboot"
    verbose_name = _("Reboot")
    url = "horizon:iot:devices:reboot"
    classes = ("ajax-modal",)
    icon = "plus"


class NetConfLink(tables.LinkAction):
    name = "netconf"
    verbose_name = _("Connections")
    url = "horizon:iot:devices:netconf"
    classes = ("ajax-modal",)
    icon = "plus"


class PingLink(tables.LinkAction):
    name = "ping"
    verbose_name = _("Ping")
    url = "horizon:iot:devices:ping"
    classes = ("ajax-modal",)
    icon = "plus"


class RestoreServices(tables.BatchAction):
    name = "restoreservices"

    @staticmethod
    def action_present(count):
        return u"Restore ALL Services"

    @staticmethod
    def action_past(count):
        return u"Restored ALL Services"

    def allowed(self, request, device=None):
        return True

    def action(self, request, device_id):
        api.iotronic.restore_services(request, device_id)


class DeleteDevicesAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Device",
            u"Delete Devices",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Device",
            u"Deleted Devices",
            count
        )
    # policy_rules = (("iot", "iot:delete_device"),)

    """
    def allowed(self, request, role):
        return api.keystone.keystone_can_edit_role()
    """

    def delete(self, request, device_id):
        api.iotronic.board_delete(request, device_id)


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
    template_name = 'iot/devices/_cell_services.html'
    context = device_info._info
    # LOG.debug("CONTEXT: %s", context)
    return template.loader.render_to_string(template_name,
                                            context)


class DevicesTable(tables.DataTable):
    name = tables.WrappingColumn('name', link="horizon:iot:devices:detail",
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
        row_actions = (EditDeviceLink, AttachPortLink, DetachPortLink,
                       PackageActionLink, UpgradeLRLink, RestartLRLink,
                       RebootLink, NetConfLink, PingLink,
                       ActionLink, RestoreServices, DeleteDevicesAction)
        table_actions = (DeviceFilterAction, CreateDeviceLink,
                         DeleteDevicesAction)
