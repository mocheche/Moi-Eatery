from django.conf.urls import url
from .views import (AccountEmailActivateView, ProfileFormView
                    )

app_name='accounts'

urlpatterns = [
    url(r'^email/confirm/(?P<key>[0-9A-Za-z]+)/$', AccountEmailActivateView.as_view(), 
            name='email-activate'),
    url(r'^email/resend-activation/$', 
            AccountEmailActivateView.as_view(), 
            name='resend-activation'),
    url(r'^profile/edit/$', ProfileFormView.as_view(), name='profile')

]

# account/email/confirm/asdfads/ -> activation view
