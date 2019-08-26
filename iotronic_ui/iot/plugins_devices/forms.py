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

import cPickle
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


class InjectPluginForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    onboot = forms.BooleanField(label=_("On Boot"), required=False)

    plugin_list = forms.MultipleChoiceField(
        label=_("Plugins List"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable', 'data-slug': 'slug-inject-plugin'}),
        help_text=_("Select plugin in this pool ")
    )

    def __init__(self, *args, **kwargs):

        super(InjectPluginForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        pluginslist_length = len(kwargs["initial"]["plugin_list"])

        self.fields["plugin_list"].choices = kwargs["initial"]["plugin_list"]
        self.fields["plugin_list"].max_length = pluginslist_length

    def handle(self, request, data):

        counter = 0

        for plugin in data["plugin_list"]:
            for key, value in self.fields["plugin_list"].choices:
                if key == plugin:

                    try:
                        inject = iotronic.plugin_inject(request,
                                                        data["uuid"],
                                                        key,
                                                        data["onboot"])
                        # LOG.debug("API: %s %s", plugin, request)
                        message_text = inject
                        messages.success(request, _(message_text))

                        if counter != len(data["plugin_list"]) - 1:
                            counter += 1
                        else:
                            return True

                    except Exception:
                        message_text = "Unable to inject plugin on device " \
                                       + str(data["name"]) + "."
                        exceptions.handle(request, _(message_text))

                    break


class CallPluginForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    # plugin_list = forms.MultipleChoiceField(
    plugin_list = forms.ChoiceField(
        label=_("Plugins List"),
        # widget=forms.SelectMultiple(
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-call-plugin'}),
        help_text=_("Select plugins in this pool ")
    )

    parameters = forms.CharField(
        label=_("Parameters"),
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-callplugin-json'}),
        help_text=_("Plugin parameters")
    )

    def __init__(self, *args, **kwargs):

        super(CallPluginForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        # pluginslist_length = len(kwargs["initial"]["plugin_list"])

        self.fields["plugin_list"].choices = kwargs["initial"]["plugin_list"]
        # self.fields["plugin_list"].max_length = pluginslist_length

    def handle(self, request, data):

        counter = 0

        if not data["parameters"]:
            data["parameters"] = {}
        else:
            data["parameters"] = json.loads(data["parameters"])

        try:
            action = iotronic.plugin_action(request,
                                            data["uuid"],
                                            data["plugin_list"],
                                            "PluginCall",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to call plugin on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class StartPluginForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    # plugin_list = forms.MultipleChoiceField(
    plugin_list = forms.ChoiceField(
        label=_("Plugins List"),
        # widget=forms.SelectMultiple(
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-start-plugin'}),
        help_text=_("Select plugins in this pool ")
    )

    parameters = forms.CharField(
        label=_("Parameters"),
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'switchable',
                   'data-slug': 'slug-startplugin-json'}),
        help_text=_("Plugin parameters")
    )

    def __init__(self, *args, **kwargs):

        super(StartPluginForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        self.fields["plugin_list"].choices = kwargs["initial"]["plugin_list"]

    def handle(self, request, data):

        counter = 0

        if not data["parameters"]:
            data["parameters"] = {}
        else:
            data["parameters"] = json.loads(data["parameters"])

        try:
            action = iotronic.plugin_action(request,
                                            data["uuid"],
                                            data["plugin_list"],
                                            "PluginStart",
                                            data["parameters"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to start plugin on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class StopPluginForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    delay = forms.IntegerField(
        label=_("Delay in secs"),
        required=False,
        help_text=_("OPTIONAL: seconds to wait before stopping the plugin")
    )

    # plugin_list = forms.MultipleChoiceField(
    plugin_list = forms.ChoiceField(
        label=_("Plugins List"),
        # widget=forms.SelectMultiple(
        widget=forms.Select(
            attrs={'class': 'switchable', 'data-slug': 'slug-stop-plugin'}),
        help_text=_("Select plugins in this pool ")
    )

    def __init__(self, *args, **kwargs):

        super(StopPluginForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})

        self.fields["plugin_list"].choices = kwargs["initial"]["plugin_list"]

    def handle(self, request, data):

        counter = 0

        if not data["delay"]:
            data["delay"] = {}
        else:
            data["delay"] = {"delay": data["delay"]}

        try:
            action = iotronic.plugin_action(request,
                                            data["uuid"],
                                            data["plugin_list"],
                                            "PluginStop",
                                            data["delay"])
            message_text = action
            messages.success(request, _(message_text))
            return True

        except Exception:
            message_text = "Unable to stop plugin on device " \
                           + str(data["name"]) + "."
            exceptions.handle(request, _(message_text))


class RemovePluginsForm(forms.SelfHandlingForm):

    uuid = forms.CharField(label=_("Device ID"), widget=forms.HiddenInput)

    name = forms.CharField(
        label=_('Device Name'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    plugin_list = forms.MultipleChoiceField(
        label=_("Plugins List"),
        widget=forms.SelectMultiple(
            attrs={'class': 'switchable', 'data-slug': 'slug-remove-plugins'}),
        help_text=_("Select plugins in this pool ")
    )

    def __init__(self, *args, **kwargs):

        super(RemovePluginsForm, self).__init__(*args, **kwargs)
        # input=kwargs.get('initial',{})
        self.fields["plugin_list"].choices = kwargs["initial"]["plugin_list"]

    def handle(self, request, data):

        counter = 0

        for plugin in data["plugin_list"]:
            for key, value in self.fields["plugin_list"].choices:
                if key == plugin:

                    try:
                        iotronic.plugin_remove(request, data["uuid"], key)

                        message_text = "Plugin " + str(value) + \
                                       " removed successfully."
                        messages.success(request, _(message_text))

                        if counter != len(data["plugin_list"]) - 1:
                            counter += 1
                        else:
                            return True

                    except Exception:
                        message_text = "Unable to remove plugin " \
                                       + str(value) + "."
                        exceptions.handle(request, _(message_text))

                    break
