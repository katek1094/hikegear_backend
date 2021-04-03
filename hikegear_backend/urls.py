from django.contrib import admin
from django.urls import path, include
from app.emails import activate_user_account_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),
    path('activate_account/<uidb64>/<token>', activate_user_account_view, name='activate_account'),
]
