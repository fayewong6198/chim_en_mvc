from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.shortcuts import reverse

User = get_user_model()


class Address(models.Model):
    ADDRESS_CHOICES = (
        ('B', 'Billing'),
        ('S', 'Shipping'),
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="addresses")
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip_code = models.CharField(max_length=255)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_1}, {self.address_line_2}, {self.city}, {self.zip_code}"

    def get_absolute_url(self):
        print("cc")
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
    image = models.ImageField(
        upload_to='product_images', blank=True, null=True)
    description = models.TextField()
    price = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # available_colors = models.ManyToManyField(ColorVariation)
    # available_sizes = models.ManyToManyField(SizeVariation)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("cart:product-detail", kwargs={"slug": self.slug})

    def get_price(self):
        return "{:.2f}".format(self.price / 100)


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

    def get_raw_total_item_price(self):
        return self.quantity * self.product.price

    def get_total_item_price(self):
        price = self.get_raw_total_item_price()
        return "{:.2f}".format(price / 100)


class FavoriteItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} x {self.product.title}"


class Order(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="orders")
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(blank=True, null=True)
    ordered = models.BooleanField(default=False)

    billing_address = models.ForeignKey(
        Address, related_name='billing_address', blank=True, null=True, on_delete=models.SET_NULL)

    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"ORDER-{self.pk}"


class Payment(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=(
        ('Paypal', 'Paypal'),
    ))
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    amount = models.FloatField()
    raw_response = models.TextField()

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
    favorite = models.ForeignKey(
        Favorite, related_name='products', on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"FavoriteProduct-{self.pk}"
