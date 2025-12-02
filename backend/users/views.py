from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
import qrcode
from io import BytesIO
import base64

from users.models import User, Teacher
from users.decorators import login_required, role_required, admin_required, security_required, teacher_required
from vehicles.models import Vehicle
from parking.models import ParkingConfig, ParkingHistory
from core.mongodb import parking_history_collection
from core.utils import str_to_objectid

# ============ AUTHENTICATION VIEWS ============

def index_view(request):
    """Trang chủ"""
    if 'user_id' in request.session:
        role = request.session.get('role')
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'security':
            return redirect('security_dashboard')
    return redirect('login')

def login_view(request):
    """Trang đăng nhập"""
    if request.user.is_authenticated or 'user_id' in request.session:
        role = request.session.get('role')
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'security':
            return redirect('security_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Xác thực
        user = User.authenticate(username, password)
        
        if user:
            # Lưu session
            request.session['user_id'] = str(user['_id'])
            request.session['username'] = user['username']
            request.session['role'] = user['role']
            request.session['full_name'] = user['full_name']
            
            messages.success(request, f"Xin chào {user['full_name']}")
            
            # Redirect theo role
            if user['role'] == 'admin':
                return redirect('admin_dashboard')
            elif user['role'] == 'teacher':
                return redirect('teacher_dashboard')
            elif user['role'] == 'security':
                return redirect('security_dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
    
    return render(request, 'login.html')

def logout_view(request):
    """Đăng xuất"""
    request.session.flush()
    messages.success(request, 'Bạn đã đăng xuất')
    return redirect('login')

# ============ ADMIN VIEWS ============

@login_required
@admin_required
def admin_dashboard(request):
    """Dashboard quản trị viên"""
    # Thống kê
    total_teachers = len(Teacher.get_all())
    total_vehicles = len(Vehicle.get_all())
    total_parkings = len(ParkingHistory.get_today())
    
    context = {
        'total_teachers': total_teachers,
        'total_vehicles': total_vehicles,
        'total_parkings': total_parkings,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@admin_required
def admin_teachers_list(request):
    """Danh sách giảng viên"""
    teachers = Teacher.get_with_user_info()
    
    # Thêm id field cho template
    for teacher in teachers:
        teacher['id'] = str(teacher['_id'])
    
    context = {
        'teachers': teachers
    }
    return render(request, 'admin/teachers_list.html', context)

@login_required
@admin_required
def admin_teachers_form(request, teacher_id=None):
    """Form tạo/cập nhật giảng viên"""
    teacher = None
    user = None
    
    if teacher_id:
        teacher = Teacher.get_by_id(teacher_id)
        if teacher:
            user = User.get_by_id(str(teacher['user_id']))
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email = request.POST.get('email', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        faculty = request.POST.get('faculty', '').strip()
        department = request.POST.get('department', '').strip()
        specialized_area = request.POST.get('specialized_area', '').strip()
        
        try:
            if teacher_id:
                # Cập nhật
                Teacher.update(teacher_id, {
                    'employee_id': employee_id,
                    'faculty': faculty,
                    'department': department,
                    'specialized_area': specialized_area
                })
                
                if user:
                    User.update(str(user['_id']), {
                        'email': email,
                        'full_name': full_name,
                        'phone': phone
                    })
                
                messages.success(request, 'Cập nhật giảng viên thành công')
            else:
                # Tạo mới
                user_id = User.create(username, password, email, full_name, phone, 'teacher')
                Teacher.create(user_id, employee_id, faculty, department, specialized_area)
                messages.success(request, 'Tạo giảng viên thành công')
            
            return redirect('admin_teachers_list')
        except ValueError as e:
            messages.error(request, str(e))
    
    context = {
        'teacher': teacher,
        'user': user
    }
    return render(request, 'admin/teachers_form.html', context)

@login_required
@admin_required
def admin_teachers_delete(request, teacher_id):
    """Xóa giảng viên"""
    teacher = Teacher.get_by_id(teacher_id)
    
    if teacher:
        Teacher.delete(teacher_id)
        User.delete(str(teacher['user_id']))
        messages.success(request, 'Xóa giảng viên thành công')
    else:
        messages.error(request, 'Không tìm thấy giảng viên')
    
    return redirect('admin_teachers_list')

# ============ TEACHER VIEWS ============

@login_required
@teacher_required
def teacher_dashboard(request):
    """Dashboard giảng viên"""
    user_id = request.session.get('user_id')
    teacher = Teacher.get_by_user_id(user_id)
    
    # Thống kê
    vehicles = Vehicle.get_by_teacher(str(teacher['_id']))
    
    # Thêm id field
    for vehicle in vehicles:
        vehicle['id'] = str(vehicle['_id'])
    
    context = {
        'teacher': teacher,
        'vehicles': vehicles
    }
    return render(request, 'teacher/dashboard.html', context)

@login_required
@teacher_required
def teacher_vehicles_list(request):
    """Danh sách xe của giảng viên"""
    user_id = request.session.get('user_id')
    teacher = Teacher.get_by_user_id(user_id)
    
    vehicles = Vehicle.get_by_teacher(str(teacher['_id']))
    
    # Thêm id field
    for vehicle in vehicles:
        vehicle['id'] = str(vehicle['_id'])
    
    context = {
        'vehicles': vehicles
    }
    return render(request, 'teacher/my_vehicles.html', context)

@login_required
@teacher_required
def teacher_vehicle_form(request, vehicle_id=None):
    """Form đăng ký/cập nhật xe"""
    user_id = request.session.get('user_id')
    teacher = Teacher.get_by_user_id(user_id)
    vehicle = None
    
    if vehicle_id:
        vehicle = Vehicle.get_by_id(vehicle_id)
    
    if request.method == 'POST':
        license_plate = request.POST.get('license_plate', '').strip().upper()
        vehicle_type = request.POST.get('vehicle_type', '').strip()
        color = request.POST.get('color', '').strip()
        brand = request.POST.get('brand', '').strip()
        
        try:
            if vehicle_id:
                # Cập nhật
                Vehicle.update(vehicle_id, {
                    'license_plate': license_plate,
                    'vehicle_type': vehicle_type,
                    'color': color,
                    'brand': brand
                })
                messages.success(request, 'Cập nhật xe thành công')
            else:
                # Tạo mới
                Vehicle.create(
                    license_plate=license_plate,
                    vehicle_type=vehicle_type,
                    color=color,
                    brand=brand,
                    teacher_id=str(teacher['_id'])
                )
                messages.success(request, 'Đăng ký xe thành công')
            
            return redirect('teacher_vehicles_list')
        except ValueError as e:
            messages.error(request, str(e))
    
    context = {
        'vehicle': vehicle
    }
    return render(request, 'teacher/vehicle_form.html', context)

@login_required
@teacher_required
def teacher_vehicle_delete(request, vehicle_id):
    """Xóa xe"""
    Vehicle.delete(vehicle_id)
    messages.success(request, 'Xóa xe thành công')
    return redirect('teacher_vehicles_list')

@login_required
@teacher_required
def teacher_my_qr(request):
    """Mã QR của giảng viên"""
    user_id = request.session.get('user_id')
    teacher = Teacher.get_by_user_id(user_id)
    
    vehicles = Vehicle.get_by_teacher(str(teacher['_id']))
    
    # Thêm QR code cho mỗi xe
    for vehicle in vehicles:
        vehicle['id'] = str(vehicle['_id'])
        
        # Tạo QR code
        qr_data = f"vehicle_{str(vehicle['_id'])}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        vehicle['qr_code'] = img_str
    
    context = {
        'vehicles': vehicles
    }
    return render(request, 'teacher/my_qr.html', context)

@login_required
@teacher_required
def teacher_parking_history(request):
    """Lịch sử đỗ xe của giảng viên"""
    user_id = request.session.get('user_id')
    teacher = Teacher.get_by_user_id(user_id)
    
    # Lấy lịch sử của tất cả xe của giảng viên
    vehicles = Vehicle.get_by_teacher(str(teacher['_id']))
    histories = []
    for vehicle in vehicles:
        histories.extend(ParkingHistory.get_by_vehicle(str(vehicle['_id'])))
    
    context = {
        'histories': histories
    }
    return render(request, 'teacher/parking_history.html', context)

# ============ SECURITY VIEWS ============

@login_required
@security_required
def security_dashboard(request):
    """Dashboard bảo vệ"""
    context = {
        'now': datetime.now()
    }
    return render(request, 'security/dashboard.html', context)

@login_required
@security_required
def security_scan_qr(request):
    """Trang quét QR Code"""
    context = {
        'now': datetime.now()
    }
    return render(request, 'security/scan_qr.html', context)

@login_required
@security_required
def security_manual_entry(request):
    """Trang nhập thủ công"""
    license_plate = request.GET.get('license_plate', '').strip().upper()
    searched = bool(license_plate)
    vehicle = None
    is_inside = False
    
    if searched:
        # Tìm xe theo biển số
        vehicle_data = Vehicle.get_by_license_plate(license_plate)
        
        if vehicle_data:
            # Lấy thông tin đầy đủ
            vehicles = Vehicle.get_with_teacher_info(str(vehicle_data['_id']))
            if vehicles:
                vehicle = vehicles[0]
                vehicle['id'] = str(vehicle['_id'])
                
                # Check if inside
                history = parking_history_collection.find_one({
                    'vehicle_id': vehicle_data['_id'],
                    'status': 'inside'
                })
                is_inside = history is not None
    
    context = {
        'license_plate': license_plate,
        'searched': searched,
        'vehicle': vehicle,
        'is_inside': is_inside
    }
    return render(request, 'security/manual_entry.html', context)

@login_required
@security_required
def security_checkout(request, vehicle_id):
    """Checkout xe"""
    vehicle = Vehicle.get_by_id(vehicle_id)
    
    if vehicle:
        # Cập nhật lịch sử đỗ xe
        parking_history_collection.update_one(
            {
                'vehicle_id': str_to_objectid(vehicle_id),
                'status': 'inside'
            },
            {
                '$set': {
                    'status': 'outside',
                    'checkout_time': datetime.now()
                }
            }
        )
        messages.success(request, f"Xe {vehicle.get('license_plate')} đã checkout")
    else:
        messages.error(request, 'Không tìm thấy xe')
    
    return redirect('security_manual_entry')

# ============ ADMIN PARKING VIEWS ============

@login_required
@admin_required
def admin_parking_history(request):
    """Lịch sử đỗ xe"""
    histories = ParkingHistory.get_today()
    
    context = {
        'histories': histories
    }
    return render(request, 'admin/parking_history.html', context)

@login_required
@admin_required
def admin_parking_config(request):
    """Cấu hình bãi đỗ xe"""
    configs = ParkingConfig.get_all()
    
    if request.method == 'POST':
        vehicle_type = request.POST.get('vehicle_type', '').strip()
        new_capacity = request.POST.get('total_slots', '').strip()
        
        try:
            new_capacity = int(new_capacity)
            ParkingConfig.update_capacity(vehicle_type, new_capacity)
            messages.success(request, 'Cập nhật cấu hình thành công')
            return redirect('admin_parking_config')
        except ValueError:
            messages.error(request, 'Vui lòng nhập số hợp lệ')
    
    context = {
        'configs': configs
    }
    return render(request, 'admin/parking_config.html', context)
