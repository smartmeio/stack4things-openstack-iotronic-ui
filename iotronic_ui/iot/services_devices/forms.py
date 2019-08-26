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


class EnableServiceForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    service_list = forms.MultipleChoiceField(
        label=_("Services List"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-select-services'}),
        help_text=_("Add available services from this pool")
    )

    def __init__(self, *args, **kwargs):
        super(EnableServiceForm, self).__init__(*args, **kwargs)
        self.fields["service_list"].choices = kwargs["initial"]["service_list"]

    def handle(self, request, data):

        counter = 0
        for service in data["service_list"]:
            try:
                action = iotronic.service_action(request, data["uuid"],
                                                 service, "ServiceEnable")

                # message_text = "Service(s) enabled successfully."
                message_text = action
                messages.success(request, _(message_text))

                if counter != len(data["service_list"]) - 1:
                    counter += 1
                else:
                    return True

            except Exception:
                message_text = "Unable to enable service."
                exceptions.handle(request, _(message_text))


class DisableServiceForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    service_list = forms.MultipleChoiceField(
        label=_("Services List"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-select-services'}),
        help_text=_("Select services to disable from this pool")
    )

    def __init__(self, *args, **kwargs):
        super(DisableServiceForm, self).__init__(*args, **kwargs)
        self.fields["service_list"].choices = kwargs["initial"]["service_list"]

    def handle(self, request, data):

        counter = 0
        for service in data["service_list"]:
            try:
                action = iotronic.service_action(request, data["uuid"],
                                                 service, "ServiceDisable")

                # message_text = "Service(s) disabled successfully."
                message_text = action
                messages.success(request, _(message_text))

                if counter != len(data["service_list"]) - 1:
                    counter += 1
                else:
                    return True

            except Exception:
                message_text = "Unable to disable service."
                exceptions.handle(request, _(message_text))
