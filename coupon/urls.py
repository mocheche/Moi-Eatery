#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 08:56:09 2019

@author: job
"""
from django.conf.urls import url
from . import views

app_name = 'coupon'


urlpatterns = [
        url(r'^apply/$', views.coupon_apply, name='apply'),
        ]

