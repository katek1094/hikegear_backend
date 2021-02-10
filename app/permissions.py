from rest_framework.permissions import BasePermission


class IsAuthenticatedOrPostOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated or view.action == 'create':
            return True
        else:
            return False


class IsOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.profile.user == request.user

