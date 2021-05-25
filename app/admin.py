from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin import ModelAdmin

from .models import MyUser, Profile, Backpack, Category, Subcategory, Brand, Product, Review
from django.contrib.sessions.models import Session
from simple_history.admin import SimpleHistoryAdmin


class SessionAdmin(ModelAdmin):
    @staticmethod
    def _session_data(obj):
        return obj.get_decoded()

    list_display = ['session_key', '_session_data', 'expire_date']


class MyUserAdmin(UserAdmin):
    model = MyUser
    list_display = ('email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active',)}
         ),
    )
    search_fields = ('email',)
    ordering = ('-date_joined',)


class CreatedUpdatedAdmin:
    readonly_fields = ['updated', 'created']


class BackpackAdmin(CreatedUpdatedAdmin, ModelAdmin):
    list_display = ['name', 'description', 'profile', 'created', 'updated', 'shared']
    list_filter = ['created', 'updated', 'shared']


class ProfileAdmin(ModelAdmin):
    @staticmethod
    def _backpacks_amount(obj):
        return len(obj.backpacks.all())

    list_display = ['user', '_backpacks_amount']


admin.site.register(Session, SessionAdmin)
admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Backpack, BackpackAdmin)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Brand, SimpleHistoryAdmin)
admin.site.register(Product, SimpleHistoryAdmin)
admin.site.register(Review, SimpleHistoryAdmin)
