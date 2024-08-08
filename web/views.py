from django.shortcuts import render, redirect
from .models import UserSubscription, SubscriptionPlan
import paypalrestsdk
from django.urls import reverse
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm

paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

def subscribe(request):
    if request.method == "POST":
        plan_id = request.POST.get('plan_id')
        print(f"Received plan_id: {plan_id}")  # Debug print
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            print(f"Found plan: {plan}")  # Debug print
        except SubscriptionPlan.DoesNotExist:
            print("Plan does not exist")  # Debug print
            return redirect('subscription_error')
        
        # Create a new subscription for the user
        user_subscription = UserSubscription.objects.create(user=request.user, plan=plan)
        
        # Create a PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse('payment_execute')),
                "cancel_url": request.build_absolute_uri(reverse('payment_failed'))
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": plan.name,
                        "sku": "plan",
                        "price": str(plan.price),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(plan.price),
                    "currency": "USD"
                },
                "description": f"Subscription to {plan.name} plan"
            }]
        })
        
        if payment.create():
            print(f"Payment created successfully: {payment}")  # Debug print
            # Find the approval URL and redirect to PayPal
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            # Handle payment creation errors
            print(f"Payment creation failed: {payment.error}")  # Debug print
            return redirect('payment_failed')

    # If not a POST request, render the subscription page
    return render(request, 'subscription.html')

def payment_execute(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    if not payment_id or not payer_id:
        # Handle the case where paymentId or PayerID is missing
        return redirect('payment_failed')

    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Payment was successful
            return redirect('payment_completed')
        else:
            # Payment failed
            print(f"Payment execution failed: {payment.error}")
            return redirect('payment_failed')
    except paypalrestsdk.ResourceNotFound as e:
        # Handle the case where the payment resource was not found
        print(f"ResourceNotFound error: {e}")
        return redirect('payment_failed')
    except Exception as e:
        # Handle other exceptions
        print(f"An error occurred: {e}")
        return redirect('payment_failed')

def payment_completed_view(request):
    return render(request, 'payment-completed.html')

def payment_failed_view(request):
    return render(request, 'payment-failed.html')

def subscription_error(request):
    return render(request, 'subscription_error.html')

def checkout_view(request):
    host = request.get_host()
    
    # Default amount
    total_amount = 0

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        # Define plan amounts
        plan_amounts = {
            '1': 10.00,  # Basic Plan
            '2': 20.00,  # Standard Plan
            '3': 30.00,  # Premium Plan
        }

        # Get the amount for the selected plan
        total_amount = plan_amounts.get(plan_id, 0.00)

        # Create PayPal payment form
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': '{:.2f}'.format(total_amount),
            'item_name': f"Subscription Plan - {plan_id}",
            'invoice': f"INVOICE_NO-{plan_id}",
            'currency_code': "USD",
            'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
            'return_url': 'http://{}{}'.format(host, reverse('payment-completed')),
            'cancel_url': 'http://{}{}'.format(host, reverse('payment-failed')),
        }

        paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)

        return render(request, 'checkout.html', {
            'total_amount': total_amount,
            'paypal_payment_button': paypal_payment_button,
        })

    # If GET request, just render the subscription options page
    return redirect('subscription')
