from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from functools import wraps

def is_enterprise_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == 'admin')

def enterprise_admin_required(view_func):
    """
    Decorator for enterprise views:
    - Anonymous users redirect to login
    - Authenticated non-admin users get 403 Forbidden
    - Admins get full access
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect anonymous users to the login page, passing the current URL as ?next=
            return redirect_to_login(request.get_full_path(), login_url='/enterprise/login/')
        
        if not is_enterprise_admin(request.user):
            # Authenticated, but not an admin/superuser
            raise PermissionDenied("Enterprise access required.")
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
