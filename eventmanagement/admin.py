from django.contrib import admin
from .models import Profile, Event

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'organization')
    search_fields = ('user__username', 'phone', 'organization')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'date_time', 'fee', 'seats', 'early_bird_enabled', 'dynamic_pricing_enabled', 'gst_enabled', 'get_registered_user_count')
    list_filter = ('type', 'early_bird_enabled', 'dynamic_pricing_enabled', 'gst_enabled')
    search_fields = ('title', 'description')
    filter_horizontal = ('registered_users',)
    readonly_fields = ('registered_users',)

    fieldsets = (
        (None, {
            'fields': ('title', 'type', 'date_time', 'description', 'fee', 'seats')
        }),
        ('Early Bird Discount', {
            'fields': ('early_bird_enabled', 'early_bird_deadline'),
            'classes': ('collapse',),
        }),
        ('Dynamic Pricing', {
            'fields': (
                'dynamic_pricing_enabled',
                'stage1_seats', 'stage1_price',
                'stage2_seats', 'stage2_price',
                'stage3_seats', 'stage3_price',
            ),
            'classes': ('collapse',),
        }),
        ('GST & Registrations', {
            'fields': ('gst_enabled', 'registered_users'),
        }),
    )

    def get_registered_user_count(self, obj):
        return obj.registered_users.count()
    get_registered_user_count.short_description = 'Registered Users'
