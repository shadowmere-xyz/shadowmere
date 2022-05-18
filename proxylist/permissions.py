from rest_framework.permissions import BasePermission, SAFE_METHODS


class GeneralPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        elif request.method == "POST":
            return request.user.is_staff
        else:
            return request.user.is_superuser
