from django.shortcuts import render, redirect
from django.contrib import messages
from users.models import User, Teacher
from users.decorators import login_required

def login_view(request):
    """Trang đăng nhập"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = User.authenticate(username, password)
        
        if user:
            # Lưu session
            request.session['user_id'] = str(user['_id'])
            request.session['username'] = user['username']
            request.session['full_name'] = user['full_name']
            request.session['role'] = user['role']
            
            messages.success(request, f'Chào mừng {user["full_name"]}!')
            
            # Redirect theo role
            if user['role'] == 'admin':
                return redirect('admin_dashboard')
            elif user['role'] == 'security':
                return redirect('security_dashboard')
            else:  # teacher
                return redirect('teacher_dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    """Đăng xuất"""
    request.session.flush()
    messages.success(request, 'Đã đăng xuất thành công')
    return redirect('login')

def index_view(request):
    """Trang chủ - redirect theo role"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    role = request.session.get('role')
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'security':
        return redirect('security_dashboard')
    else:
        return redirect('teacher_dashboard')
# ============ ADMIN DASHBOARD ============
@login_required
@admin_required
def admin_dashboard(request):
    """Dashboard Admin"""
    # Statistics
    total_teachers = len(Teacher.get_all())
    total_vehicles = len(Vehicle.get_all())
    parking_configs = ParkingConfig.get_all()
    parking_stats = ParkingHistory.get_statistics()
    
    # Chart data - xe theo loại
    vehicle_types = Vehicle.count_by_type()
    
    context = {
        'total_teachers': total_teachers,
        'total_vehicles': total_vehicles,
        'parking_configs': parking_configs,
        'parking_stats': parking_stats,
        'vehicle_types': vehicle_types
    }
    return render(request, 'admin/dashboard.html', context)


# ============ SECURITY DASHBOARD ============
@login_required
@security_required
def security_dashboard(request):
    """Dashboard Bảo vệ"""
    # Xe đang trong bãi
    current_parking = ParkingHistory.get_current_parking()
    parking_configs = ParkingConfig.get_all()
    parking_stats = ParkingHistory.get_statistics()
    
    context = {
        'current_parking': current_parking,
        'parking_configs': parking_configs,
        'parking_stats': parking_stats
    }
    return render(request, 'security/dashboard.html', context)


# ============ TEACHER DASHBOARD ============

@login_required
@teacher_required
def teacher_dashboard(request):
    """Dashboard Giảng viên"""
    teacher = Teacher.get_by_user_id(request.session['user_id'])
    vehicles = Vehicle.get_by_teacher(str(teacher['_id']))
    
    # Lịch sử gần đây
    recent_history = []
    for vehicle in vehicles:
        history = ParkingHistory.get_by_vehicle(str(vehicle['_id']), limit=5)
        recent_history.extend(history)
    
    # Sort by time
    recent_history.sort(key=lambda x: x['time_in'], reverse=True)
    recent_history = recent_history[:10]  # Top 10
    
    context = {
        'teacher': teacher,
        'vehicles': vehicles,
        'recent_history': recent_history
    }
    return render(request, 'teacher/dashboard.html', context)
