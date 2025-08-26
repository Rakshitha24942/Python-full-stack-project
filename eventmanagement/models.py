from django.db import models
from django.contrib.auth.models import User

# Existing Profile model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    organization = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username


# Updated Event model with dynamic pricing fields

class Event(models.Model):
    title = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    date_time = models.DateTimeField()
    fee = models.DecimalField(max_digits=6, decimal_places=2)
    seats = models.IntegerField()
    early_bird_enabled = models.BooleanField(default=False)
    dynamic_pricing_enabled = models.BooleanField(default=False)
    gst_enabled = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    # ✅ Add these two new fields:
    early_bird_deadline = models.DateTimeField(null=True, blank=True)
    registered_users = models.ManyToManyField(User, blank=True)

    # Dynamic pricing fields
    stage1_seats = models.IntegerField(null=True, blank=True)
    stage1_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    stage2_seats = models.IntegerField(null=True, blank=True)
    stage2_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    stage3_seats = models.IntegerField(null=True, blank=True)
    stage3_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.title



# New Registration model for tracking event registrations
class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=20, default='free')  # 'free' or 'paid'
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')  # prevent duplicate registrations

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"
