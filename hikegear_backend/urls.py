from django.contrib import admin
from django.urls import path, include
from app.functions.emails import activate_user_account_view
from app.views import stats_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),
    path('activate_account/<uidb64>/<token>', activate_user_account_view, name='activate_account'),
    path('stats', stats_view, name='stats'),
]

handler404 = 'app.views.page_not_found_view'
