from rest_framework.permissions import BasePermission


class IsAuthenticatedOrPostOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.method == 'POST'


class IsOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.profile.user == request.user

