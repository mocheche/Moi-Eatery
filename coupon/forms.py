#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 08:39:00 2019

@author: job
"""

from django import forms

class CouponApplyForm(forms.Form):
    code = forms.CharField()
    
    
    
    
    