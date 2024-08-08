from celery import shared_task
from .models import UserSubscription
from twilio.rest import Client
from django.conf import settings
from datetime import datetime, timedelta

@shared_task
def check_subscriptions():
    now = datetime.now()
    expiring_soon = UserSubscription.objects.filter(end_date__lte=now + timedelta(days=3))
    expired = UserSubscription.objects.filter(end_date__lt=now)

    for subscription in expiring_soon:
        send_sms(subscription.user.phone_number, f"Your subscription will expire on {subscription.end_date}. Please renew.")

    for subscription in expired:
        send_sms(subscription.user.phone_number, "Your subscription has expired.")

def send_sms(to, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to
    )
