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

# from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tabs

LOG = logging.getLogger(__name__)


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("iot/devices/_detail_overview.html")

    def get_context_data(self, request):

        coordinates = self.tab_group.kwargs['device'].__dict__['location'][0]
        ports = self.tab_group.kwargs['device']._info['ports']
        services = self.tab_group.kwargs['device']._info['services']
        webservices = self.tab_group.kwargs['device']._info['webservices']
        plugins = self.tab_group.kwargs['device']._info['plugins']

        return {"device": self.tab_group.kwargs['device'],
                "coordinates": coordinates,
                "services": services,
                "webservices": webservices,
                "ports": ports,
                "plugins": plugins,
                "is_superuser": request.user.is_superuser}


class DeviceDetailTabs(tabs.TabGroup):
    slug = "device_details"
    # tabs = (OverviewTab, LogTab, ConsoleTab, AuditTab)
    tabs = (OverviewTab,)
    sticky = True
