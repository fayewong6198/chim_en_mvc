from django.contrib import admin
from .models import SizeVariation, Product, Order, OrderItem, Payment, ColorVariation, FavoriteItem, ProductImage, Category


class ProductImageInline(admin.TabularInline):
    extra = 1
    model = ProductImage


class ProductAdmin(admin.ModelAdmin):
    inlines = (ProductImageInline,)


admin.site.register(Product, ProductAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(ColorVariation)
admin.site.register(FavoriteItem)
admin.site.register(Category)

# Register your models here.
