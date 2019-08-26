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

from django.conf.urls import url

from iotronic_ui.iot.devices import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^create/$', views.CreateView.as_view(), name='create'),
    url(r'^(?P<device_id>[^/]+)/update/$', views.UpdateView.as_view(),
        name='update'),
    url(r'^(?P<device_id>[^/]+)/detail/$', views.DeviceDetailView.as_view(),
        name='detail'),
    url(r'^(?P<device_id>[^/]+)/attachport/$',
        views.AttachPortView.as_view(), name='attachport'),
    url(r'^(?P<device_id>[^/]+)/detachport/$',
        views.DetachPortView.as_view(), name='detachport'),
    url(r'^(?P<device_id>[^/]+)/netconf/$',
        views.NetConfView.as_view(), name='netconf'),
    url(r'^(?P<device_id>[^/]+)/ping/$',
        views.PingView.as_view(), name='ping'),
    url(r'^(?P<device_id>[^/]+)/action/$',
        views.ActionView.as_view(), name='action'),
    url(r'^(?P<device_id>[^/]+)/packageaction/$',
        views.PackageActionView.as_view(), name='packageaction'),
    url(r'^(?P<device_id>[^/]+)/upgradelr/$',
        views.UpgradeLRView.as_view(), name='upgradelr'),
    url(r'^(?P<device_id>[^/]+)/restartlr/$',
        views.RestartLRView.as_view(), name='restartlr'),
    url(r'^(?P<device_id>[^/]+)/reboot/$',
        views.RebootView.as_view(), name='reboot'),
]
