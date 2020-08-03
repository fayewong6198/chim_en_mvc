from django.shortcuts import render, redirect
from django.views import generic
from .utils import get_or_set_order_session, get_or_set_favorite_session
from django.shortcuts import get_object_or_404, reverse
from .forms import AddToCartForm, PaymentForm
from django.http import HttpResponseRedirect
# Create your views here.

from .models import Product, OrderItem, FavoriteProduct


class ProductListView(generic.TemplateView):
    template_name = 'product_list.html'

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        liked = []
        for like_item in FavoriteProduct.objects.filter(user=self.request.user):
            liked.append(like_item.product.id)
        context['liked'] = liked


class ProductDetailView(generic.FormView):
    template_name = 'product.html'
    form_class = AddToCartForm

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse("cart:summary")
        # return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))

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
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['object'] = self.get_object()
        return context


class CartView(generic.TemplateView):
    template_name = "order_summary.html"

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        context["object"] = get_or_set_order_session(self.request)
        return context


class CheckOutView(generic.TemplateView):
    template_name = "payment.html"

    def get_context_data(self, **kwargs):
        context = super(CheckOutView, self).get_context_data(**kwargs)
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


class TymOrUnTym(generic.View):

    def get(self, request, *args, **kwargs):

        product = Product.objects.get(pk=kwargs['product_id'])
        try:

            favorite = FavoriteProduct.objects.get(
                product=product.id, user=request.user)
            print("Delete")
            favorite.delete()
        except FavoriteProduct.DoesNotExist:
            print("add new")
            new_favorite = FavoriteProduct()
            new_favorite.user = request.user
            new_favorite.product = product
            new_favorite.save()

        request.session['products_in_favorite'] = FavoriteProduct.objects.filter(
            user=request.user).count()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # if favorite_item:
        #     favorite_item.delete()
        # else:
        #     favorite = get_or_set_favorite_session(self.request)
        #     product = self.get_object()

        #     new_tym = Favorite()
        #     new_tym.product = product
        #     new_tym.order = favorite
        #     new_tym.save()


class PaymentView(generic.FormView):
    template_name = 'payment.html'
    form_class = PaymentForm

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)
        context["object"] = get_or_set_order_session(self.request)
        return context
