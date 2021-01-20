from rest_framework.permissions import BasePermission


class IsAuthenticatedOrPostOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated or view.action == 'create':
            return True
        else:
            return False
