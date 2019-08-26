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

from iotronic_ui.iot.webservices_devices import views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<device_id>[^/]+)/detail/$', views.DeviceDetailView.as_view(),
        name='detail'),
    url(r'^(?P<device_id>[^/]+)/enablewebservice/$',
        views.EnableWebServiceView.as_view(), name='enablewebservice'),
    url(r'^(?P<device_id>[^/]+)/disablewebservice/$',
        views.DisableWebServiceView.as_view(), name='disablewebservice'),
]