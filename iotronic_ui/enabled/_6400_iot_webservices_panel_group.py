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

from django.utils.translation import ugettext_lazy as _

# The slug of the panel group to be added to HORIZON_CONFIG. Required.
PANEL_GROUP = 'iot_webservices'
# The display name of the PANEL_GROUP. Required.
PANEL_GROUP_NAME = _('Web Services')
# The slug of the dashboard the PANEL_GROUP associated with. Required.
PANEL_GROUP_DASHBOARD = 'iot'
