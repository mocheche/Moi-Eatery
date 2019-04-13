from decimal import Decimal
from django.shortcuts import render, get_object_or_404, reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from paypal.standard.forms import PayPalPaymentsForm

from orders.models import Order

@login_required
def payment_process(request):
	order_id = request.session.get('order_id')
	order   = get_object_or_404(Order,id=order_id)
	host    = request.get_host()

	paypal_dict ={
	       'business':settings.PAYPAL_RECEIVER_EMAIL,
	       'amount'  : '%.2f'% order.get_total_cost().quantize(Decimal('.01')),
	       'item_name': 'Order {}'.format(order.id),
	       'invoice' : str(order.id),
	       'currency_code':'Ksh',
	       'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
	       'cancel_return':'http://{}{}'.format(host,'payment:cancel'),
	       	}
	form = PayPalPaymentsForm(initial=paypal_dict)
	return render(request,'payment/process.html',{'order':order,'form':form})

@csrf_exempt
def payment_done(request):
	return render(request,'payment/done.html')


@csrf_exempt
def payment_canceled(request):
	return render(request,'payment/canceled.html')