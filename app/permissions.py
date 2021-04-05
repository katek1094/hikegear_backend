from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrPostOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.method == 'POST'


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.profile.user == request.user


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.profile.user == request.user


class BackpackPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            if obj.private:
                return obj.profile.user == request.user
            else:
                return True
        else:
            return obj.profile.user == request.user
