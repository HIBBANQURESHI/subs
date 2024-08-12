from django.shortcuts import render, redirect
from .models import UserSubscription, SubscriptionPlan
import paypalrestsdk
from django.urls import reverse
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
from django.core.mail import send_mail
from django.template.loader import render_to_string


def subscribe(request):
    if request.method == "POST":
        plan_id = request.POST.get('plan_id')
        print(f"Received plan_id: {plan_id}")  
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            print(f"Found plan: {plan}")  
        except SubscriptionPlan.DoesNotExist:
            print("Plan does not exist")  
            return redirect('subscription_error')
        
        # Creating a new subscription for the user
        user_subscription = UserSubscription.objects.create(user=request.user, plan=plan)
        
        # Creating a PayPal payment
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
            print(f"Payment created successfully: {payment}")  
           
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
           
            print(f"Payment creation failed: {payment.error}") 
            return redirect('payment_failed')

    
    return render(request, 'subscription.html')

def payment_execute(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    if not payment_id or not payer_id:
        return redirect('payment_failed')

    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Payment was successful
            # Send confirmation email
            user_subscription = UserSubscription.objects.get(user=request.user, plan__id=request.session.get('plan_id'))

            # Email content
            subject = f"Subscription Confirmation for {user_subscription.plan.name} Plan"
            message = render_to_string('subscription_email.html', {
                'username': request.user.username,
                'plan_name': user_subscription.plan.name,
                'amount': user_subscription.plan.price,
                'start_date': user_subscription.start_date,
                'end_date': user_subscription.end_date,
            })

            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )

            return redirect('payment_completed')
        else:
            return redirect('payment_failed')
    except paypalrestsdk.ResourceNotFound as e:
        return redirect('payment_failed')
    except Exception as e:
        return redirect('payment_failed')

def payment_completed_view(request):
    return render(request, 'payment-completed.html')

def payment_failed_view(request):
    return render(request, 'payment-failed.html')

def subscription_error(request):
    return render(request, 'subscription_error.html')

def checkout_view(request):
    host = request.get_host()
    
   
    total_amount = 0

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
       
        plan_amounts = {
            '1': 10.00,            
            '2': 20.00, 
            '3': 30.00, 
        }

        
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

    
    return redirect('subscription')
