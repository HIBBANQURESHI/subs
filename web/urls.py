from django.urls import path
from . import views

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('payment/execute/', views.payment_execute, name='payment_execute'),
    path('payment-completed/', views.payment_completed_view, name='payment-completed'),
    path('payment-failed/', views.payment_failed_view, name='payment-failed'),
    path('subscription_error/', views.subscription_error, name='subscription_error'),
    path('checkout/', views.checkout_view, name='checkout'),
]
