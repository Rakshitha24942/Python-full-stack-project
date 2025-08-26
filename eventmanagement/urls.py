from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),

    # Event management
    path('events/', views.event_list_view, name='event_list'),
    path('events/add/', views.event_create_view, name='event_add'),
    path('events/edit/<int:pk>/', views.event_edit_view, name='event_edit'),
    path('events/delete/<int:pk>/', views.event_delete_view, name='event_delete'),

    # Event detail and registration
    path('events/<int:pk>/', views.event_detail_view, name='event_detail'),

    # Price breakdown before registration
    path('events/<int:pk>/price-breakdown/', views.event_price_breakdown_view, name='event_price_breakdown'),

    path('events/<int:pk>/register/', views.register_event_view, name='register_event'),

    # Stripe integration
    path('stripe-checkout/<int:event_id>/', views.stripe_checkout_view, name='stripe_checkout'),
    path('stripe-success/', views.stripe_success_view, name='stripe_success'),
    path('stripe-cancel/', views.stripe_cancel_view, name='stripe_cancel'),

    # Dynamic pricing configuration
    path('events/<int:pk>/dynamic-pricing/', views.dynamic_pricing_view, name='dynamic_pricing'),
    path('download-ticket/<int:event_id>/', views.download_ticket_view, name='download_ticket'),
]
