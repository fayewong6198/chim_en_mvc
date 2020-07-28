from django.contrib import admin
from .models import SizeVariation, Product, Order, OrderItem, Payment, ColorVariation

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(ColorVariation)
admin.site.register(SizeVariation)

# Register your models here.
