from django.shortcuts import render, redirect
from django.contrib import messages
from users.models import User, Teacher
from users.decorators import login_required, admin_required, security_required, teacher_required
from vehicles.models import Vehicle
from parking.models import ParkingHistory, ParkingConfig

# ============ LOGIN/LOGOUT ============
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
    total_teachers = len(Teacher.get_all())
    total_vehicles = len(Vehicle.get_all())
    parking_configs = ParkingConfig.get_all()
    parking_stats = ParkingHistory.get_statistics()
    
    context = {
        'total_teachers': total_teachers,
        'total_vehicles': total_vehicles,
        'parking_configs': parking_configs,
        'parking_stats': parking_stats
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@admin_required
def admin_teachers_list(request):
    """Danh sách giảng viên"""
    teachers = Teacher.get_with_user_info()
    
    context = {
        'teachers': teachers,
        'total_teachers': len(teachers)
    }
    return render(request, 'admin/teachers_list.html', context)

@login_required
@admin_required
def admin_teachers_form(request, teacher_id=None):
    """Form thêm/sửa giảng viên"""
    teacher = None
    if teacher_id:
        teachers = Teacher.get_with_user_info(teacher_id)
        teacher = teachers[0] if teachers else None
    
    if request.method == 'POST':
        # User data
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        
        # Teacher data
        employee_id = request.POST.get('employee_id')
        faculty = request.POST.get('faculty')
        department = request.POST.get('department')
        specialized_area = request.POST.get('specialized_area')
        
        try:
            if teacher_id:
                # Update user
                User.update(teacher['user_id'], {
                    'email': email,
                    'full_name': full_name,
                    'phone': phone
                })
                
                # Update teacher
                Teacher.update(teacher_id, {
                    'employee_id': employee_id,
                    'faculty': faculty,
                    'department': department,
                    'specialized_area': specialized_area
                })
                messages.success(request, 'Cập nhật giảng viên thành công')
            else:
                # Create user
                user_id = User.create(username, password, email, full_name, phone, 'teacher')
                
                # Create teacher
                Teacher.create(str(user_id), employee_id, faculty, department, specialized_area)
                messages.success(request, 'Thêm giảng viên thành công')
            
            return redirect('admin_teachers_list')
        except ValueError as e:
            messages.error(request, str(e))
    
    context = {
        'teacher': teacher
    }
    return render(request, 'admin/teachers_form.html', context)

@login_required
@admin_required
def admin_teachers_delete(request, teacher_id):
    """Xóa giảng viên"""
    try:
        teacher = Teacher.get_by_id(teacher_id)
        if teacher:
            User.delete(str(teacher['user_id']))
            Teacher.delete(teacher_id)
            messages.success(request, 'Xóa giảng viên thành công')
        else:
            messages.error(request, 'Không tìm thấy giảng viên')
    except Exception as e:
        messages.error(request, f'Lỗi: {str(e)}')
    
    return redirect('admin_teachers_list')

@login_required
@admin_required
def admin_parking_history(request):
    """Lịch sử ra vào bãi xe"""
    history = ParkingHistory.get_today()
    
    # Get full info with aggregation
    pipeline = [
        {'$match': {'time_in': {'$gte': history[0]['time_in']}} if history else {}},
        {
            '$lookup': {
                'from': 'vehicles',
                'localField': 'vehicle_id',
                'foreignField': '_id',
                'as': 'vehicle'
            }
        },
        {'$unwind': '$vehicle'},
        {
            '$lookup': {
                'from': 'teachers',
                'localField': 'vehicle.teacher_id',
                'foreignField': '_id',
                'as': 'teacher'
            }
        },
        {'$unwind': '$teacher'},
        {
            '$lookup': {
                'from': 'users',
                'localField': 'teacher.user_id',
                'foreignField': '_id',
                'as': 'user'
            }
        },
        {'$unwind': '$user'},
        {'$sort': {'time_in': -1}}
    ]
    
    from core.mongodb import parking_history_collection
    history_full = list(parking_history_collection.aggregate(pipeline))
    
    context = {
        'history': history_full,
        'total': len(history_full)
    }
    return render(request, 'admin/parking_history.html', context)

@login_required
@admin_required
def admin_parking_config(request):
    """Cấu hình bãi xe"""
    configs = ParkingConfig.get_all()
    
    if request.method == 'POST':
        vehicle_type = request.POST.get('vehicle_type')
        new_capacity = int(request.POST.get('capacity'))
        
        try:
            ParkingConfig.update_capacity(vehicle_type, new_capacity)
            messages.success(request, 'Cập nhật cấu hình thành công')
            return redirect('admin_parking_config')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    
    context = {
        'configs': configs
    }
    return render(request, 'admin/parking_config.html', context)

# ============ SECURITY DASHBOARD ============
@login_required
@security_required
def security_dashboard(request):
    """Dashboard Bảo vệ"""
    current_parking = ParkingHistory.get_current_parking()
    parking_configs = ParkingConfig.get_all()
    parking_stats = ParkingHistory.get_statistics()
    
    # Convert nested ObjectId fields to string IDs for templates (avoid attributes starting with underscore)
    for rec in current_parking:
        try:
            rec['vehicle_id'] = str(rec.get('vehicle', {}).get('_id'))
            # also expose vehicle id as 'id' within vehicle dict for templates if needed
            if 'vehicle' in rec and rec['vehicle'] and '_id' in rec['vehicle']:
                rec['vehicle']['id'] = str(rec['vehicle']['_id'])
            if 'user' in rec and rec['user'] and '_id' in rec['user']:
                rec['user']['id'] = str(rec['user']['_id'])
        except Exception:
            pass

    context = {
        'current_parking': current_parking,
        'parking_configs': parking_configs,
        'parking_stats': parking_stats
    }
    return render(request, 'security/dashboard.html', context)


# ============ SECURITY HELPERS ============
@login_required
@security_required
def security_scan_qr(request):
    """Placeholder for QR scanning interface (can be implemented later)"""
    messages.info(request, 'Chức năng quét QR chưa được triển khai trong môi trường phát triển.')
    return redirect('security_dashboard')


@login_required
@security_required
def security_manual_entry(request):
    """Placeholder for manual entry interface"""
    messages.info(request, 'Chức năng nhập thủ công chưa được triển khai trong môi trường phát triển.')
    return redirect('security_dashboard')


@login_required
@security_required
def security_checkout(request, vehicle_id):
    """Check-out a vehicle by vehicle_id (called from dashboard)"""
    try:
        ParkingHistory.checkout(vehicle_id, security_id=request.session.get('user_id'))
        messages.success(request, 'Check-out thành công')
    except Exception as e:
        messages.error(request, f'Không thể check-out: {str(e)}')
    return redirect('security_dashboard')

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
    recent_history = recent_history[:10]
    
    context = {
        'teacher': teacher,
        'vehicles': vehicles,
        'recent_history': recent_history
    }
    return render(request, 'teacher/dashboard.html', context)