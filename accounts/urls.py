
from . import views

from django.urls import path, include
from django.conf.urls import url
from accounts.API.apis import RegisterAPI, LoginAPI
urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('changePassword/', views.changePassword, name='change-password'),
    path('api/auth/register', RegisterAPI.as_view()),
    path('api/auth/login', LoginAPI.as_view()),
    # path('payment/', views.userPayments, name='user_payments'),
    # path('payment/<int:id>', views.userPayment, name='user_payment'),

    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),

]
