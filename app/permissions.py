from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrPostOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.method == 'POST'


class BackpackPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            if obj.shared:
                return True
            else:
                return obj.profile.user == request.user
        else:
            return obj.profile.user == request.user


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user.profile
