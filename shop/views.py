from django.shortcuts import render ,get_object_or_404
from django.core.paginator import Paginator

from .recommender import Recommender
from .models import Category,Product
from cart.forms import CartAddProductForm

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    product_list   = Product.objects.filter(available = True)

    if category_slug:
        category = get_object_or_404(Category,slug=category_slug)
        product_list = product_list.filter(category = category)

    paginator  = Paginator(product_list,4)
    page       =  request.GET.get('page')
    products   = paginator.get_page(page)


    return render(request,
                  'shop/product/list.html',
                  {'category': category,
                   'categories': categories,
                   'products': products})

def product_detail(request ,id ,slug):
    product = get_object_or_404(Product,id=id,slug=slug,available=True)
    cart_product_form = CartAddProductForm()
    r = Recommender()
    recommended_products = r.suggest_products_for([product], 4)

    return render(request, 'shop/product/detail.html',{'product':product,
                            'cart_product_form':cart_product_form ,
                            ' recommended_products': recommended_products})

