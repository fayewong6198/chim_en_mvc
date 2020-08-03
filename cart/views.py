from django.shortcuts import render, redirect
from django.views import generic
from .utils import get_or_set_order_session, get_or_set_favorite_session
from django.shortcuts import get_object_or_404, reverse
from .forms import AddToCartForm
from django.http import HttpResponseRedirect
# Create your views here.

from .models import Product, OrderItem, FavoriteProduct, Favorite


class ProductListView(generic.ListView):
    template_name = 'product_list.html'
    queryset = Product.objects.all()


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

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get(sefl, request, *args, **kwargs):
        favorite_item = get_object_or_404(FavoriteProduct, id=kwargs['pk'])
        if favorite_item:
            favorite_item.delete()
        else:
            favorite = get_or_set_favorite_session(self.request)
            product = self.get_object()
            new_tym = Favorite()
            new_tym.product = product
            new_tym.order = favorite
            new_tym.save()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
