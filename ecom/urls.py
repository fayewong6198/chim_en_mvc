from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from core import views

# API
from accounts.API import apis as account_apis
from cart.API import apis as cart_apis
router = routers.DefaultRouter()

router.register(r'users', account_apis.UserViewSet)
router.register(r'products', cart_apis.ProductViewSet)
router.register(r'payments', cart_apis.PaymentViewSet)
router.register(r'order-items', cart_apis.OrderItemViewSet)
router.register(r'orders', cart_apis.OrderViewSet)

router.register(r'blog_images', cart_apis.BlogImageViewSet)
router.register(r'categories', cart_apis.CategoryViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.HomeView.as_view(), name='home'),
    path('', views.HomeView.as_view(), name='index'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('cart/', include('cart.urls', namespace='cart')),
    path('accounts/', include('accounts.urls')),
    # API
    path('api/', include(router.urls)),
    path('api/products/images',
         cart_apis.ProductImageView.as_view(), name='product-image'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # path('api/auth/', include('knox.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
