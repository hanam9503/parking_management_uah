from django.shortcuts import render, redirect
from django.contrib import messages
from users.models import User, Teacher
from users.decorators import login_required, admin_required, security_required, teacher_required
from vehicles.models import Vehicle
from parking.models import ParkingHistory, ParkingConfig

# ============ LOGIN/LOGOUT ============
def login_view(request):
    """Trang đăng nhập"""
    # Nếu đã đăng nhập, redirect theo role
    if 'user_id' in request.session:
        role = request.session.get('role', '')
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'security':
            return redirect('security_dashboard')
        else:
            return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin')
            return render(request, 'login.html')
        
        # Authenticate
        user = User.authenticate(username, password)
        
        if user:
            # Lưu session
            request.session['user_id'] = str(user['_id'])
            request.session['username'] = user['username']
            request.session['full_name'] = user['full_name']
            request.session['role'] = user['role']
            
            # Force save session
            request.session.modified = True
            
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
    full_name = request.session.get('full_name', '')
    request.session.flush()
    messages.success(request, f'Tạm biệt {full_name}! Đã đăng xuất thành công')
    return redirect('login')

def index_view(request):
    """Trang chủ - redirect theo role"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    role = request.session.get('role', '')
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'security':
        return redirect('security_dashboard')
    elif role == 'teacher':
        return redirect('teacher_dashboard')
    else:
        # Nếu role không hợp lệ, logout
        request.session.flush()
        return redirect('login')

# ============ ADMIN DASHBOARD ============
@login_required
@admin_required
def admin_dashboard(request):
    """Dashboard Admin"""
    try:
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
    except Exception as e:
        messages.error(request, f'Lỗi tải dashboard: {str(e)}')
        return redirect('login')

@login_required
@admin_required
def admin_teachers_list(request):
    """Danh sách giảng viên"""
    try:
        teachers = Teacher.get_with_user_info()
        
        context = {
            'teachers': teachers,
            'total_teachers': len(teachers)
        }
        return render(request, 'admin/teachers_list.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi tải danh sách: {str(e)}')
        return redirect('admin_dashboard')

@login_required
@admin_required
def admin_teachers_form(request, teacher_id=None):
    """Form thêm/sửa giảng viên"""
    teacher = None
    if teacher_id:
        teachers = Teacher.get_with_user_info(teacher_id)
        teacher = teachers[0] if teachers else None
        
        if not teacher:
            messages.error(request, 'Không tìm thấy giảng viên')
            return redirect('admin_teachers_list')
    
    if request.method == 'POST':
        # User data
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        email = request.POST.get('email', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Teacher data
        employee_id = request.POST.get('employee_id', '').strip()
        faculty = request.POST.get('faculty', '').strip()
        department = request.POST.get('department', '').strip()
        specialized_area = request.POST.get('specialized_area', '').strip()
        
        # Validate
        if not teacher_id and (not username or not password):
            messages.error(request, 'Username và password không được để trống')
            return render(request, 'admin/teachers_form.html', {'teacher': teacher})
        
        if not all([email, full_name, phone, employee_id, faculty, department]):
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc')
            return render(request, 'admin/teachers_form.html', {'teacher': teacher})
        
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
                    'specialized_area': specialized_area if specialized_area else None
                })
                messages.success(request, 'Cập nhật giảng viên thành công')
            else:
                # Create user
                user_id = User.create(username, password, email, full_name, phone, 'teacher')
                
                # Create teacher
                Teacher.create(str(user_id), employee_id, faculty, department, 
                             specialized_area if specialized_area else None)
                messages.success(request, f'Thêm giảng viên {full_name} thành công')
            
            return redirect('admin_teachers_list')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    
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
            # Soft delete user
            User.delete(str(teacher['user_id']))
            # Delete teacher
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
    try:
        from core.mongodb import parking_history_collection
        from datetime import datetime
        
        # Get today's start
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Aggregation pipeline
        pipeline = [
            {'$match': {'time_in': {'$gte': today_start}}},
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
        
        history_full = list(parking_history_collection.aggregate(pipeline))
        
        context = {
            'history': history_full,
            'total': len(history_full)
        }
        return render(request, 'admin/parking_history.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi tải lịch sử: {str(e)}')
        return redirect('admin_dashboard')

@login_required
@admin_required
def admin_parking_config(request):
    """Cấu hình bãi xe"""
    configs = ParkingConfig.get_all()
    
    if request.method == 'POST':
        vehicle_type = request.POST.get('vehicle_type')
        try:
            new_capacity = int(request.POST.get('capacity', 0))
            
            if new_capacity < 0:
                messages.error(request, 'Sức chứa phải là số dương')
            else:
                ParkingConfig.update_capacity(vehicle_type, new_capacity)
                messages.success(request, f'Cập nhật sức chứa {vehicle_type} thành công')
            
            return redirect('admin_parking_config')
        except ValueError:
            messages.error(request, 'Sức chứa phải là số nguyên')
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
    try:
        current_parking = ParkingHistory.get_current_parking()
        parking_configs = ParkingConfig.get_all()
        parking_stats = ParkingHistory.get_statistics()
        
        # Convert ObjectId to string for templates
        for rec in current_parking:
            try:
                rec['vehicle_id'] = str(rec.get('vehicle', {}).get('_id'))
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
    except Exception as e:
        messages.error(request, f'Lỗi tải dashboard: {str(e)}')
        return redirect('login')

@login_required
@security_required
def security_scan_qr(request):
    """Placeholder for QR scanning"""
    messages.info(request, 'Chức năng quét QR đang được phát triển')
    return redirect('security_dashboard')

@login_required
@security_required
def security_manual_entry(request):
    """Placeholder for manual entry"""
    messages.info(request, 'Chức năng nhập thủ công đang được phát triển')
    return redirect('security_dashboard')

@login_required
@security_required
def security_checkout(request, vehicle_id):
    """Check-out xe"""
    try:
        ParkingHistory.checkout(vehicle_id, security_id=request.session.get('user_id'))
        messages.success(request, 'Check-out thành công')
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f'Lỗi check-out: {str(e)}')
    
    return redirect('security_dashboard')

# ============ TEACHER DASHBOARD ============
@login_required
@teacher_required
def teacher_dashboard(request):
    """Dashboard Giảng viên"""
    try:
        # Lấy teacher profile
        user_id = request.session.get('user_id')
        teacher = Teacher.get_by_user_id(user_id)
        
        if not teacher:
            # Log chi tiết để debug
            import sys
            print(f"DEBUG: Không tìm thấy teacher với user_id={user_id}", file=sys.stderr)
            messages.error(request, f'Không tìm thấy thông tin giảng viên. User ID: {user_id}')
            # Không flush session, chỉ redirect
            return redirect('login')
        
        # Lấy user info để hiển thị đầy đủ
        from core.mongodb import users_collection
        user = users_collection.find_one({'_id': teacher['user_id']})
        teacher['user'] = user if user else {}
        
        # Lấy vehicles
        try:
            vehicles = Vehicle.get_by_teacher(str(teacher['_id']))
            vehicles = vehicles if vehicles else []
            # Thêm field 'id' từ '_id' để dùng trong template
            for vehicle in vehicles:
                vehicle['id'] = str(vehicle['_id'])
        except Exception as e:
            print(f"DEBUG: Lỗi lấy danh sách xe: {str(e)}", file=__import__('sys').stderr)
            vehicles = []
        
        # Lấy QR codes cho vehicles
        for vehicle in vehicles:
            try:
                from vehicles.models import QRCode
                qr_code = QRCode.get_by_vehicle(str(vehicle['_id']))
                vehicle['qr_code'] = qr_code if qr_code else None
            except Exception as e:
                print(f"DEBUG: Lỗi lấy QR code xe {vehicle.get('_id')}: {str(e)}", file=__import__('sys').stderr)
                vehicle['qr_code'] = None
        
        # Lấy lịch sử gần đây
        recent_history = []
        for vehicle in vehicles:
            try:
                history = ParkingHistory.get_by_vehicle(str(vehicle['_id']), limit=5)
                recent_history.extend(history if history else [])
            except Exception as e:
                print(f"DEBUG: Lỗi lấy lịch sử xe {vehicle.get('_id')}: {str(e)}", file=__import__('sys').stderr)
                continue
        
        # Sort by time - với kiểm tra an toàn
        try:
            recent_history.sort(key=lambda x: x.get('time_in', 0), reverse=True)
        except Exception as e:
            print(f"DEBUG: Lỗi sort lịch sử: {str(e)}", file=__import__('sys').stderr)
        
        recent_history = recent_history[:10]
        
        context = {
            'teacher': teacher,
            'vehicles': vehicles,
            'recent_history': recent_history
        }
        return render(request, 'teacher/dashboard.html', context)
        
    except Exception as e:
        import traceback
        error_msg = f'Lỗi tải dashboard: {str(e)}'
        traceback.print_exc()
        print(f"FULL ERROR: {error_msg}", file=__import__('sys').stderr)
        messages.error(request, error_msg)
        return redirect('login')