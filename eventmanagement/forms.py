from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    organization = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'organization', 'password1', 'password2']


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'type', 'date_time', 'fee', 'seats',
            'early_bird_enabled', 'dynamic_pricing_enabled', 'gst_enabled', 'description',
            'stage1_seats', 'stage1_price',
            'stage2_seats', 'stage2_price',
            'stage3_seats', 'stage3_price',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and not user.is_staff:
            for field in [
                'early_bird_enabled', 'dynamic_pricing_enabled', 'gst_enabled',
                'stage1_seats', 'stage1_price',
                'stage2_seats', 'stage2_price',
                'stage3_seats', 'stage3_price',
            ]:
                self.fields.pop(field)
