from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.shortcuts import reverse

User = get_user_model()


class City(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=255)
    city = models.ForeignKey(
        City, max_length=25, on_delete=models.CASCADE, related_name='districts')
    ship_fee = models.FloatField(default=25000)

    def __str__(self):
        return self.name


class Address(models.Model):
    ADDRESS_CHOICES = (
        ('B', 'Billing'),
        ('S', 'Shipping'),
    )
    address = models.CharField(max_length=255, null=True, blank=True)
    districts = models.ForeignKey(
        District, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, blank=True, null=True)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)

    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address}, {self.districts}, {self.city}"

    def get_absolute_url(self):

        print(reverse("cart:product-detail", kwargs={"slug": self.slug}))
        return reverse("cart:product-detail", kwargs={"slug": self.slug})

    class Meta:
        verbose_name_plural = "Addresses"


class ColorVariation(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class SizeVariation(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Category(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products', null=True)

    description = models.TextField()
    full_description = models.TextField(null=True, blank=True, default="")
    price = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    promotion = models.IntegerField(default=0)
    # available_colors = models.ManyToManyField(ColorVariation)
    # available_sizes = models.ManyToManyField(SizeVariation)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("cart:product-detail", kwargs={"slug": self.slug})

    def get_price(self):
        return self.price

    def get_promotion_price(self):
        if self.promotion != 0:
            return self.price-self.promotion/100*self.price


class BlogImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="blog_images", blank=True, null=True)
    image = models.ImageField(upload_to='blogs/')

    def __str__(self):
        return self.image.url


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.image.url


class OrderItem(models.Model):
    order = models.ForeignKey(
        "Order", related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    # color = models.ForeignKey(
    #     ColorVariation, on_delete=models.CASCADE, blank=True, null=True)

    # size = models.ForeignKey(
    #     SizeVariation, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def get_total_item_price(self):
        if self.product.promotion > 0:
            return self.quantity * self.product.get_promotion_price()
        else:
            return self.quantity * self.product.price


class Order(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="orders")
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(blank=True, null=True)
    ordered = models.BooleanField(default=False)
    order_address = models.ForeignKey(
        Address, related_name='order_addresses', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"ORDER-{self.pk}"

    def get_total_price(self):
        price = 0
        for item in self.items.all():
            price = price + item.get_total_item_price()
        return price


class Payment(models.Model):
    STATUS_CHOICES = (
        ('S', 'spending'),
        ('P', 'Processing'),
        ('C', 'Complete'),

    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=(
        ('Paypal', 'Paypal'),
    ))
    timestamp = models.DateTimeField(auto_now_add=True)
    # successful = models.BooleanField(default=False)
    amount = models.FloatField()
    raw_response = models.TextField()
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='S')

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"PAYMENT-{self.order}-{self.pk}"


def pre_save_product_receicer(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.title)


pre_save.connect(pre_save_product_receicer, sender=Product)


class Favorite(models.Model):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorite')

    def __str__(self):
        return f"Favorite-{self.pk}"


class FavoriteProduct(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites', blank=True, null=True)

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"FavoriteProduct-{self.pk}"
