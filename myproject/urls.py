from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('social_django.urls', namespace='social')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('eventmanagement.urls')),  # Change here: no 'register/' prefix
    
    # Optional: Redirect root to events list or home page if you want
    # path('', RedirectView.as_view(url='/events/', permanent=False)),
]
