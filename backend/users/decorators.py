from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def login_required(view_func):
    """Decorator yêu cầu đăng nhập"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.warning(request, 'Vui lòng đăng nhập để tiếp tục')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(*roles):
    """Decorator yêu cầu role cụ thể"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if 'user_id' not in request.session:
                messages.warning(request, 'Vui lòng đăng nhập để tiếp tục')
                return redirect('login')
            
            user_role = request.session.get('role')
            if user_role not in roles:
                messages.error(request, 'Bạn không có quyền truy cập trang này')
                return redirect('teacher_dashboard' if user_role == 'teacher' else 'login')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def admin_required(view_func):
    """Decorator yêu cầu admin"""
    return role_required('admin')(view_func)

def security_required(view_func):
    """Decorator yêu cầu security"""
    return role_required('security')(view_func)

def teacher_required(view_func):
    """Decorator yêu cầu teacher"""
    return role_required('teacher')(view_func)