from django.urls import path
from . import views
app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='summary'),
    path('shop/', views.ProductListView.as_view(), name='product-list'),
    path('<slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('increase-quantity/<pk>', views.IncreaseQuantityView.as_view(),
         name='increase-quantity'),
    path('descrease-quantity/<pk>', views.DecreaseQuantityView.as_view(),
         name='descrease-quantity'),
    path('remove_from_cart/<pk>', views.RemoveFromCartView.as_view(),
         name='remove_from_cart'),
    path('check_out/', views.CheckOutView.as_view(),
         name='check_out'),
    path('tym_or_unTym/', views.TymOrUnTym.as_view(),
         name='tym'),
]
