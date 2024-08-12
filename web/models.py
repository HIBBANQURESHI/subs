from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField(default=timedelta(days=30))  #duration 30 days

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)  

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + self.plan.duration
        super(UserSubscription, self).save(*args, **kwargs)

# Updated check_subscriptions command
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired_subscriptions = UserSubscription.objects.filter(end_date__lt=now, is_active=True)

        for subscription in expired_subscriptions:
            subscription.is_active = False
            subscription.save()
            self.stdout.write(f"Deactivated subscription for user {subscription.user.username}")