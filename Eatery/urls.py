"""Eatery URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url ,include
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView, RedirectView


from accounts.views import LoginView, RegisterView, GuestRegisterView

urlpatterns = [
    url(r'^accounts/login/$', RedirectView.as_view(url='/login')),
    url(r'^accounts/$', RedirectView.as_view(url='/account')),
    url(r'^account/', include("accounts.urls", namespace='account')),
    url(r'^accounts/', include("accounts.passwords.urls")),
    url(r'^accounts/', include("accounts.urls")),
    url(r'^register/guest/$', GuestRegisterView.as_view(), name='guest_register'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^accounts/', include('allauth.urls')),


    path('admin/', admin.site.urls),
    url(r'^payment/', include('payment.urls', namespace='payment')),
    path('',include('shop.urls', namespace='shop')),
    url('^orders/', include('orders.urls' ,namespace='orders')),
    path('cart/',include('cart.urls', namespace='cart')),
    url(r'^paypal/', include('paypal.standard.ipn.urls')),
    url(r'^coupon/', include('coupon.urls', namespace='coupon')),
    url(r'^rosetta/', include('rosetta.urls')),
    url(r'^search/', include("search.urls", namespace='search')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                           document_root=settings.MEDIA_ROOT)