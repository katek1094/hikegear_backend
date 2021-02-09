from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import ModelAdmin

from .models import MyUser, Profile, Backpack
from django.contrib.sessions.models import Session


class SessionAdmin(ModelAdmin):
    @staticmethod
    def _session_data(obj):
        return obj.get_decoded()
    list_display = ['session_key', '_session_data', 'expire_date']


class MyUserAdmin(UserAdmin):
    model = MyUser
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active', )}
         ),
    )
    search_fields = ('email', )
    ordering = ('email', )


admin.site.register(Session, SessionAdmin)
admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Profile)
admin.site.register(Backpack)
