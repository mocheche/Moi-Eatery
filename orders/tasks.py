#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 20:45:57 2019

@author: job
"""

from celery import task
from django.core.mail import send_mail

from . models import Order

@task
def order_created(order_id):
    '''
    Task to send an email notification when an order has been
    successifully created
    '''
    order = Order.objects.get(id=order_id)
    subject = 'Order nr.{}'.format(order.id)
    message = 'Dear {},\n\nYou have successifully placed your order.\
               Your order id is {}'.format(order.first_name,order.id)
    mail_sent = send_mail(
            subject,
            message,
            'admin@Eatery.com',
            [order.email])
    return mail_sent
    
