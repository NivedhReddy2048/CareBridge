from rest_framework import permissions

class IsDoctor(permissions.BasePermission):
    """
    Allows access only to users with the 'doctor' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'doctor')


class IsPatient(permissions.BasePermission):
    """
    Allows access only to users with the 'patient' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'patient')


class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to users with the 'admin' role or is_staff.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'admin' or request.user.is_staff)
        )
