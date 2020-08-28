from django.shortcuts import render, redirect
from django.views import generic
from .utils import get_or_set_order_session, get_or_set_favorite_session
from django.shortcuts import get_object_or_404, reverse
from .forms import AddToCartForm, PaymentForm, CustommerInformationForm
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import status
from django.contrib.messages import get_messages
from django.utils import timezone
import random
import binascii
import os
from django.dispatch import receiver

# Create your views here.

from .models import Product, OrderItem, FavoriteProduct, Payment, CustommerDetail, ProductDetail, District, City, Category, Review
from django.utils.decorators import method_decorator
from .choices import limit_choices as l, price_choices, sort_choice
from django.contrib import messages
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import reverse
from paypal.standard.forms import PayPalPaymentsForm
from django.views.decorators.csrf import csrf_exempt
import stripe
import json
from django.http import JsonResponse

from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
import requests


class ProductListView(generic.TemplateView):
    template_name = 'product_list.html'

    def get_context_data(self, **kwargs):
        limit = 6
        if ('limit' in self.request.GET):
            limit = self.request.GET['limit']
        products = Product.objects.all().prefetch_related("images")

        # Category
        category = ''
        if "category" in self.request.GET:
            category = self.request.GET['category']
            if category:
                try:
                    print("ahih")
                    category = Category.objects.get(title=category)
                    products = products.filter(category=category)
                except:
                    products = products.filter(category=None)

        # Search
        search = ''
        if "search" in self.request.GET:
            search = self.request.GET['search']
            if search:
                products = products.filter(title__icontains=search)

        # Sort
        sort = ''
        if "sort" in self.request.GET:
            sort = self.request.GET['sort']
            if sort:
                products = products.order_by(sort)
        # paginator
        paginator = Paginator(products, limit)
        page = 1
        if ('page' in self.request.GET):
            page = self.request.GET['page']
        paged_listings = paginator.get_page(page)

        context = super(ProductListView, self).get_context_data(**kwargs)
        context['products'] = paged_listings
        liked = []
        if self.request.user.is_authenticated:
            for like_item in FavoriteProduct.objects.filter(user=self.request.user):
                liked.append(like_item.product.id)

            self.request.session['products_in_favorite'] = FavoriteProduct.objects.filter(
                user=self.request.user).count()
        categories = Category.objects.all().prefetch_related('products')

        # Choices
        limit_choices = l
        context['limit'] = limit
        context['limit_choices'] = limit_choices
        context['sort_choices'] = sort_choice
        context['sort'] = sort
        context['categories'] = categories
        context['category'] = category
        context['search'] = search
        context['liked'] = liked

        return context


class ProductDetailView(generic.FormView):
    template_name = 'product.html'
    form_class = AddToCartForm

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse("cart:summary")

    def get_form_kwargs(self):
        kwargs = super(ProductDetailView, self).get_form_kwargs()
        kwargs['product_id'] = self.get_object().id

        return kwargs

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        product = self.get_object()

        item_filter = order.items.filter(
            product=product)

        if item_filter.exists():
            item = item_filter.first()
            item.quantity = int(form.cleaned_data['quantity'])
            item.save()

        else:
            new_item = form.save(commit=False)
            new_item.product = product
            new_item.order = order
            new_item.save()

        return super(ProductDetailView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        limit = 1

        if 'limit' in self.request.GET:
            limit = self.request.GET['limit']

        context = super(ProductDetailView, self).get_context_data(**kwargs)
        categories = Category.objects.all().prefetch_related('products')

        reviews = Review.objects.filter(
            product=self.get_object()).order_by('-created_at')
        # paginator
        paginator = Paginator(reviews, limit)
        page = 1
        if ('page' in self.request.GET):
            page = self.request.GET['page']
        paged_listings = paginator.get_page(page)

        try:
            liked = None
            if self.request.user.is_authenticated:
                liked = FavoriteProduct.objects.get(
                    user=self.request.user, product=self.get_object())
        except FavoriteProduct.DoesNotExist:
            liked = None

        if ('review_limit' in self.request.GET):
            reviews = reviews[:int(self.request.GET['review_limit'])]
        context['object'] = self.get_object()
        context['categories'] = categories
        context['reviews'] = paged_listings
        context['liked'] = liked
        return context


class CartView(generic.TemplateView):
    template_name = "order_summary.html"

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        categories = Category.objects.all().prefetch_related('products')
        context['categories'] = categories
        context["object"] = get_or_set_order_session(self.request)

        return context


class CheckOutView(generic.TemplateView):
    template_name = "payment.html"

    def get_context_data(self, **kwargs):
        context = super(CheckOutView, self).get_context_data(**kwargs)
        categories = Category.objects.all().prefetch_related('products')
        context['categories'] = categories
        context["object"] = get_or_set_order_session(self.request)

        return context


class IncreaseQuantityView(generic.View):
    def get(sefl, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])

        order_item.quantity += 1

        order_item.save()

        return redirect("cart:summary")


class DecreaseQuantityView(generic.View):
    def get(sefl, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        if order_item.quantity <= 1:
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save()
        return redirect("cart:summary")


class RemoveFromCartView(generic.View):
    def get(sefl, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.delete()
        return redirect("cart:summary")


def addToCart(request, id):

    quantity = request.POST['quantity']
    product = get_object_or_404(Product, pk=id)
    if (request.method == 'POST'):

        if product.available < int(quantity):
            return JsonResponse(data={'msg': 'Out of Stock'}, status=400)

        order = get_or_set_order_session(request)
        print(id)

        # Get all products in cart
        productsInCart = OrderItem.objects.filter(order=order)

        found = False
        for productInCart in productsInCart:
            if product.id == productInCart.product.id:
                print(True)
                productInCart.quantity = productInCart.quantity + int(quantity)
                productInCart.save()
                found = True

        if found == False:
            p = OrderItem.objects.create(
                order=order, product=product, quantity=quantity)
            p.save()

        productsInCart = OrderItem.objects.filter(
            order=order).prefetch_related('product')

        count = 0
        total = 0

        for p in productsInCart:
            # count = count + p.quantity
            count = count + p.quantity
            total = total + p.product.price * p.quantity

        # request.session['productsInCart'] = serialize('json', productsInCart)
        request.session['products_in_cart'] = count

        context = {
            'cart': {
                'products_in_cart': count
            }, "message": "added"

        }

        return JsonResponse(context)


def TymOrUnTym(request, product_id):

    if request.user.is_authenticated:
        if request.method == 'GET':
            liked = True
            product = Product.objects.get(pk=product_id)
            try:
                favorite = FavoriteProduct.objects.get(
                    product=product.id, user=request.user)
                favorite.delete()
                liked = False

            except FavoriteProduct.DoesNotExist:

                new_favorite = FavoriteProduct()
                new_favorite.user = request.user
                new_favorite.product = product
                new_favorite.save()

            count = FavoriteProduct.objects.filter(
                user=request.user).count()
            return JsonResponse({'liked': liked, 'count': count})
    return JsonResponse({'messages': "login_required"})


class PaymentView(generic.FormView):
    template_name = 'payment.html'
    form_class = PaymentForm

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)
        categories = Category.objects.all().prefetch_related('products')
        context['categories'] = categories
        context["object"] = get_or_set_order_session(self.request)
        return context


def payment_information(request):
    form = CustommerInformationForm()
    if request.method == "GET":
        if request.session['products_in_cart'] <= 0:
            messages.warning(request, "no product to buy")
            return redirect('/cart/shop')
        if (request.user.is_authenticated):
            form = CustommerInformationForm(instance=request.user)
        user_info = None
        if ('user_info' in request.session):
            user_info = request.session['user_info']

        districts = District.objects.all()
        cities = City.objects.all()
        categories = Category.objects.all().prefetch_related('products')
        return render(request, 'payment_information.html', {'form': form, 'user_info': user_info, 'districts': districts, 'cities': cities, 'categories': categories})

    if request.method == "POST":
        request.session['user_info'] = request.POST

        return redirect("/cart/payment_products")
    return redirect('/cart/payment_information')


@csrf_exempt
def payment_products(request):
    if request.session['products_in_cart'] <= 0:
        messages.warning(request, "no product to buy")
        return redirect('/cart/shop')
    user_info = request.session.get('user_info')
    cart = get_or_set_order_session(request)
    district = District.objects.get(
        id=user_info['district'])
    ship = district.ship_fee
    user_info['totalprice'] = cart.get_total_price + ship
    address = request.session['user_info']['address'] + " , " + \
        district.name+" , "+district.city.name
    user_info['ship'] = ship
    print(user_info)
    print(json.dumps(user_info))
    print(json.dumps({"abc": "123"}))
    paypal_dict = {
        "business": "sb-fv0pj3054200@business.example.com",
        "amount": user_info['totalprice']/23000,
        "item_name": "name of the item",
        "invoice": binascii.hexlify(os.urandom(24)),
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return": request.build_absolute_uri(reverse('cart:payment_success')),
        "cancel_return": request.build_absolute_uri(reverse('cart:payment_failed')),
        # Custom command to correlate to some function later (optional)
        "custom": json.dumps(user_info),

    }
    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)

    # _________________stripe payment ______________________
    stripe.api_key = 'sk_test_51HJtaHBn6v3g7KPu9jYJX4x9Q2jX92kJVUlFYTAb3M2dCCxjJS515k29FFVeOW9SwrM7Jq1UJP7KAFw6dUQGq3f500R8q7o8qx'

    if request.method == "POST":

        intent = stripe.PaymentIntent.create(
            amount=int(user_info['totalprice']),
            currency='vnd',
        )
        try:
            return JsonResponse({'publishableKey':
                                 'pk_test_51HJtaHBn6v3g7KPuU6KqFf8ZqwkUyczB7wJaiGfgDZzkEdGPLXeLEHiVEQut4HqIytOTdmrZlWp2FspBtz9FdWR5005S2ISLgs', 'clientSecret': intent.client_secret})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=403)

    categories = Category.objects.all().prefetch_related('products')

    return render(request, 'payment_products.html', {'object': cart, 'user_info': user_info, 'form': form, 'address': address, 'categories': categories})


def payment_process(request):
    print("cc")
    categories = Category.objects.all()
    if request.session['products_in_cart'] <= 0:
        messages.warning(request, "no product to buy")
        return redirect('/cart/shop')
    if (request.method == 'POST'):
        payment = None
        # Create Payment
        try:

            user = request.session['user_info']
            district = District.objects.get(
                id=user['district'])
            print(1)
            payment = Payment.objects.create()
            print(2)
            user_info = CustommerDetail.objects.create()
            user_info.payment = payment
            user_info.full_name = user['full_name']
            user_info.email = user['email']
            user_info.mobile = user['mobile']
            user_info.dictrict = district.name
            user_info.city = district.city.name
            user_info.address = user['address']
            print(3)
            user_info.save()
            print(1)
            # Create Product details
            cart = get_or_set_order_session(request)
            total_price = 0
            print(cart)

            for item in cart.items.all():
                product = get_object_or_404(Product, id=item.product.id)
                if product.available < item.quantity:
                    messages.error(request, "Out of stock")
                    return render(request, 'payment_process.html', {'success': False, 'categories': categories, 'msg': 'Out of Stock'})

            for item in cart.items.all():
                total_price = total_price + item.get_total_item_price()
                image = item.product.images.all().first()
                product = ProductDetail(payment=payment,
                                        product_id=item.product.id,
                                        product_name=item.product.title,
                                        image=image,
                                        product_amount=item.quantity,
                                        product_price=item.product.price,
                                        product_promotion=item.product.promotion)
                product.save()
                store_product = get_object_or_404(Product, id=item.product.id)
                store_product.available = store_product.available - item.quantity
                store_product.save()
            print(3)

            payment.amount = total_price+request.session['user_info']['ship']
            if 'payByCart' in request.POST:
                payment.status = 'PAID'

            payment.ship = request.session['user_info']['ship']
            payment.note = request.POST.get('note')
            if (request.user.is_authenticated):
                payment.user = request.user
            print("before save")
            print(payment.created_at)
            print(payment.created_at)
            payment.save()
            print("afters")
            cart.delete()
            print(11)
            request.session['products_in_cart'] = 0
            print(22)
            messages.success(request, "payment successfully")
            print(33)
            if 'payByCart' in request.POST:
                payment.status = 'PAID'
                payment.save()
                return JsonResponse({}, status=status.HTTP_200_OK)
            return render(request, 'payment_process.html', {'success': True, 'categories': categories})
        except Exception as e:
            # Delete payment
            print(e)
            print("cc")
            if (payment is not None):
                payment.delete()
            return render(request, 'payment_process.html', {'success': False})
            pass
    else:
        return redirect('/')


def payment_success(request):
    if (request.method == 'GET'):
        messages = list(get_messages(request))
        if (len(messages) < 1):
            return redirect('index')

        categories = Category.objects.all().prefetch_related("products")
        return render(request, 'payment_process.html', {'success': True, 'categories': categories})


def payment_failed(request):
    if (request.method == 'GET'):
        messages = list(get_messages(request))
        if (len(messages) < 1):
            return redirect('index')
        categories = Category.objects.all().prefetch_related("products")

        return render(request, 'payment_process.html', {'success': False, 'categories': categories})


def review(request):
    if (request.method == 'POST'):
        print(request.POST)
        product = get_object_or_404(Product, pk=request.POST['product'])
        params = request.POST
        review = Review.objects.create(product=product,
                                       full_name=params['full_name'], subject=params['subject'], content=params['content'], rating=params['rating'])
        print(request.POST)

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def reply(request):
    if (request.method == 'POST'):
        review = get_object_or_404(review, request.POST['review'])


@receiver(valid_ipn_received)
def payment_notification(sender, **kwargs):

    ipn_obj = sender

    print(ipn_obj.custom)
    

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        # WARNING !
        # Check that the receiver email is the same we previously
        # set on the `business` field. (The user could tamper with
        # that fields on the payment form before it goes to PayPal)
        if ipn_obj.receiver_email != "receiver_email@example.com":
            # Not a valid payment
            return

        # ALSO: for the same reason, you need to check the amount
        # received, `custom` etc. are all what you expect or what
        # is allowed.

        # Undertake some action depending upon `ipn_obj`.

        print("Paypal success")
    else:
        print("Paypal failed")


valid_ipn_received.connect(payment_notification)
