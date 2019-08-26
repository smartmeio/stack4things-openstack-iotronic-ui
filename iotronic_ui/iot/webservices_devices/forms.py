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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.api import iotronic
# from iotronic_ui.api import iotronic
from openstack_dashboard import policy

LOG = logging.getLogger(__name__)


class EnableWebServiceForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    dns = forms.CharField(label=_("Domain Name Server"))

    # zone = forms.CharField(label=_("Zone"))
    zones_list = forms.ChoiceField(
        label=_("Zones List"),
        help_text=_("Select a zone from the list")
    )

    email = forms.CharField(label=_("Email"))

    def __init__(self, *args, **kwargs):
        super(EnableWebServiceForm, self).__init__(*args, **kwargs)

        zone_choices = kwargs["initial"]["zones_list"]
        self.fields["zones_list"].choices = zone_choices

    def handle(self, request, data):

        try:
            iotronic.webservice_enable(request, data["uuid"],
                                       data["dns"], data["zones_list"],
                                       data["email"])

            messages.success(request, _("Web Service enabled on device " +
                                        str(data["name"]) + "."))
            return True

        except Exception:
            message_text = "Unable to enable web service."
            exceptions.handle(request, _(message_text))


class DisableWebServiceForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    def __init__(self, *args, **kwargs):
        super(DisableWebServiceForm, self).__init__(*args, **kwargs)

    def handle(self, request, data):

        try:
            iotronic.webservice_disable(request, data["uuid"])

            messages.success(request, _("Web Service disabled on device " +
                                        str(data["name"]) + "."))
            return True

        except Exception:
            message_text = "Unable to disable web service."
            exceptions.handle(request, _(message_text))

