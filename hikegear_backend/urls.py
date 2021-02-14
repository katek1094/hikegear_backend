from django.contrib import admin
from django.urls import path, include
from app.emails import activate_user_account

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('activate_account/<uidb64>/<token>', activate_user_account, name='activate_account'),
]
