from django import forms
from .models import SubscriptionPlan, UserSubscription

class SubscriptionForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=SubscriptionPlan.objects.all(), required=True)

    def __init__(self, *args, **kwargs):
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        self.fields['plan'].label = "Choose a Subscription Plan"
