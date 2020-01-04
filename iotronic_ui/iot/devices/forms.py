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

import json
import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import iotronic
# from iotronic_ui.api import iotronic
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


class CreateDeviceForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Device Name"))
    code = forms.CharField(
        label=_("Registration Code"),
        help_text=_("Registration code")
    )

    # MODIFY ---> options: yun, server
    type = forms.ChoiceField(
        label=_("Type"),
        # choices=[('gateway', _('Gateway')), ('server', _('Server'))],
        choices=[('raspberry', _('Arancino')), ('yun', _('Arduino YUN')), 
            ('generic', _('Generic')), ('raspberry', _('Raspberry')),
            ('server', _('Server'))],
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-type'},
        )
    )

    mobile = forms.BooleanField(label=_("Mobile"), required=False)

    latitude = forms.FloatField(label=_("Latitude"))
    longitude = forms.FloatField(label=_("Longitude"))
    altitude = forms.FloatField(label=_("Altitude"))

    def handle(self, request, data):
        try:

            # Float
            # data["location"] = [{"latitude": data["latitude"],
            #                      "longitude": data["longitude"],
            #                      "altitude": data["altitude"]}]
            # String
            data["location"] = [{"latitude": str(data["latitude"]),
                                 "longitude": str(data["longitude"]),
                                 "altitude": str(data["altitude"])}]
            # LOG.debug('DATA: %s', data)
            iotronic.device_create(request, data["code"],
                                   data["mobile"], data["location"],
                                   data["type"], data["name"])

            messages.success(request, _("Device created successfully."))
            return True

        except Exception:
            exceptions.handle(request, _('Unable to create device.'))


class UpdateDeviceForm(forms.SelfHandlingForm):
    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)
    name = forms.CharField(label=_("Device Name"))

    fleet_list = forms.ChoiceField(
        label=_("Fleets List"),
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-fleet'}),
        help_text=_("Select fleet in this pool "),
        required=False
    )

    mobile = forms.BooleanField(label=_("Mobile"), required=False)

    def __init__(self, *args, **kwargs):

        super(UpdateDeviceForm, self).__init__(*args, **kwargs)

        # Populate fleets
        fleets = iotronic.fleet_list(self.request, None)
        fleets.sort(key=lambda b: b.name)

        fleet_list = []
        fleet_list.append((None, _("-")))
        for fleet in fleets:
            fleet_list.append((fleet.uuid, _(fleet.name)))

        # LOG.debug("FLEETS: %s", fleet_list)
        self.fields["fleet_list"].choices = fleet_list
        self.fields["fleet_list"].initial = kwargs["initial"]["fleet_id"]

        # Admin
        if policy.check((("iot", "iot:update_boards"),), self.request):
            # LOG.debug("ADMIN")
            pass

        # Manager or Admin of the iot project
        elif (policy.check((("iot", "iot_manager"),), self.request) or
              policy.check((("iot", "iot_admin"),), self.request)):
            # LOG.debug("NO-edit IOT ADMIN")
            pass

        # Other users
        else:
            if self.request.user.id != kwargs["initial"]["owner"]:
                # LOG.debug("IMMUTABLE FIELDS")
                self.fields["name"].widget.attrs = {'readonly': 'readonly'}
                self.fields["mobile"].widget.attrs = {'disabled': 'disabled'}
                self.fields["fleet_list"].widget.attrs = {'disabled':
                                                          'disabled'}

    def handle(self, request, data):

        try:
            if data["fleet_list"] == '':
                data["fleet_list"] = None

            iotronic.device_update(request, data["uuid"],
                                   {"name": data["name"],
                                    "fleet": data["fleet_list"],
                                    "mobile": data["mobile"]})
            messages.success(request, _("Device updated successfully."))
            return True

        except Exception:
            exceptions.handle(request, _('Unable to update device.'))


class AttachPortForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    networks_list = forms.ChoiceField(
        label=_("Networks List"),
        help_text=_("Select network:subnet from the list")
    )

    def __init__(self, *args, **kwargs):

        super(AttachPortForm, self).__init__(*args, **kwargs)

        net_choices = kwargs["initial"]["networks_list"]
        self.fields["networks_list"].choices = net_choices

    def handle(self, request, data):
        array = data["networks_list"].split(':')
        LOG.debug(array)
        network_id = array[0]
        subnet_id = array[1]

        try:
            attach = iotronic.attach_port(request, data["uuid"],
                                          network_id, subnet_id)

            # LOG.debug("ATTACH: %s", attach)
            ip = attach._info["ip"]

            message_text = "Attached  port to ip " + str(ip) + \
                           " on device " + str(data["name"]) + \
                           " completed successfully"
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to attach port on device " + \
                           str(data["name"])

            exceptions.handle(request, _(message_text))


class DetachPortForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    port_list = forms.MultipleChoiceField(
        label=_("Ports List"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable', 'data-slug': 'slug-detacj-ports'}),
        help_text=_("Select one or more of the following attached ports")
    )

    def __init__(self, *args, **kwargs):

        super(DetachPortForm, self).__init__(*args, **kwargs)
        self.fields["port_list"].choices = kwargs["initial"]["ports"]

    def handle(self, request, data):
        # LOG.debug("DATA: %s %s", data, len(data["port_list"]))

        counter = 0

        for port in data["port_list"]:
            try:
                iotronic.detach_port(request, data["uuid"], port)

                message_text = "Detach port " + str(port) + \
                               " from device " + str(data["name"]) + \
                               " completed successfully"
                messages.success(request, _(message_text))

                if counter != len(data["port_list"]) - 1:
                    counter += 1
                else:
                    return True

            except Exception:
                message_text = "Unable to detach port " + str(port) + \
                               " from device " + str(data["name"])

                exceptions.handle(request, _(message_text))


class ActionDeviceForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    # action_list = forms.MultipleChoiceField(
    action_list = forms.ChoiceField(
        label=_("Actions List"),
        # widget=forms.SelectMultiple(
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-action-device'}),
        help_text=_("Select action in this pool ")
    )

    parameters = forms.CharField(
        label=_("Parameters"),
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-actiondevice-json'}),
        help_text=_("Action parameters")
    )

    def __init__(self, *args, **kwargs):

        super(ActionDeviceForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        self.fields["action_list"].choices = kwargs["initial"]["action_list"]

    def handle(self, request, data):

        counter = 0

        if not data["parameters"]:
            data["parameters"] = {}
        else:
            data["parameters"] = json.loads(data["parameters"])

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            data["action_list"],
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call action " \
                           + str(data["action_list"]) + " on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class PackageActionDeviceForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    manager_list = forms.ChoiceField(
        label=_("Manager"),
        widget=forms.Select(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-packageaction-manager'}),
        help_text=_("Select a manager in this pool ")
    )

    command_list = forms.ChoiceField(
        label=_("Command"),
        widget=forms.Select(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-packageaction-command'}),
        help_text=_("Select a command in this pool ")
    )

    packages = forms.CharField(
        label=_("Package"),
        # required=False,
        widget=forms.Textarea(
            attrs={'class': 'switchable',
                   'rows':2,
                   'data-slug': 'slug-package'}),
        help_text=_("Package name")
    )

    options = forms.CharField(
        label=_("Options"),
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'switchable',
                   'rows':2,
                   'data-slug': 'slug-options-json'}),
        help_text=_("Package options")
    )

    version = forms.CharField(
        label=_("Version"),
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'switchable',
                   'rows':1,
                   'data-slug': 'slug-version-json'}),
        help_text=_("Package version")
    )

    def __init__(self, *args, **kwargs):

        super(PackageActionDeviceForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        self.fields["manager_list"].choices = kwargs["initial"]["manager_list"]
        self.fields["command_list"].choices = kwargs["initial"]["command_list"]

    def handle(self, request, data):

        counter = 0

        if not data["options"]: data["options"] = ""
        if not data["version"]: data["version"] = ""

        data["parameters"] = {"manager": data["manager_list"],
                              "command": data["command_list"],
                              "package": data["packages"],
                              "options": data["options"],
                              "version": data["version"]}

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            "DevicePkgOperation",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call package action " \
                           + "DevicePkgOperation on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class MountActionDeviceForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    # mount_action_list = forms.MultipleChoiceField(
    mount_action_list = forms.ChoiceField(
        label=_("Mount actions List"),
        # widget=forms.SelectMultiple(
        widget=forms.Select(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-mountaction-device'}),
        help_text=_("Select action in this pool ")
    )

    def __init__(self, *args, **kwargs):

        super(MountActionDeviceForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        mount_actions = kwargs["initial"]["mount_action_list"]
        self.fields["mount_action_list"].choices = mount_actions

    def handle(self, request, data):

        counter = 0

        data["parameters"] = {"mnt_cmd": data["mount_action_list"]}

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            "DeviceMountFs",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call action " \
                           + str(data["mount_action_list"]) + " on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class UpgradeLRForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    delay = forms.IntegerField(
        label=_("Delay"),
        required=False,
        help_text=_("Delay in seconds")
    )

    version = forms.CharField(
        label=_("Version"),
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'switchable',
                   'rows':1,
                   'data-slug': 'slug-version-json'}),
        help_text=_("Package version")
    )

    update_conf = forms.BooleanField(
        label=_("Update Configuration"),
        required=False
    )

    def handle(self, request, data):

        counter = 0

        if not data["delay"]: data["delay"] = 3
        if not data["version"]: data["version"] = ""

        data["parameters"] = {"delay": data["delay"],
                              "version": data["version"],
                              "update_conf": data["update_conf"]}

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            "DeviceUpgradeLR",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call DeviceUpgradeLR on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class RestartLRForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    delay = forms.IntegerField(
        label=_("Delay"),
        required=False,
        help_text=_("Delay in seconds")
    )

    def handle(self, request, data):

        counter = 0

        if not data["delay"]: data["delay"] = 3

        data["parameters"] = {"delay": data["delay"]}

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            "DeviceRestartLR",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call DeviceRestartLR on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class RebootForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    delay = forms.IntegerField(
        label=_("Delay"),
        required=False,
        help_text=_("Delay in seconds")
    )

    def handle(self, request, data):

        counter = 0

        if not data["delay"]: data["delay"] = 3

        data["parameters"] = {"delay": data["delay"]}

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            "DeviceReboot",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call DeviceReboot on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class NetConfForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    def handle(self, request, data):

        counter = 0

        data["parameters"] = {}

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            "DeviceNetConfig",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call DeviceNetConfig on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class PingForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    def handle(self, request, data):

        counter = 0

        data["parameters"] = {}

        try:
            action = iotronic.device_action(request,
                                            data["uuid"],
                                            "DevicePing",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call DevicePing on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))
