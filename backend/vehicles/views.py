from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib import messages
from users.decorators import login_required, admin_required, teacher_required
from vehicles.models import Vehicle, QRCode
from users.models import Teacher
from parking.models import ParkingHistory

# ============ ADMIN VIEWS ============

@login_required
@admin_required
def admin_vehicles_list(request):
    """Danh sách xe (Admin)"""
    vehicles = Vehicle.get_with_teacher_info()
    
    # Thêm field 'id' từ '_id' để dùng trong template
    for vehicle in vehicles:
        vehicle['id'] = str(vehicle['_id'])
    
    context = {
        'vehicles': vehicles,
        'total_vehicles': len(vehicles)
    }
    return render(request, 'admin/vehicles_list.html', context)

@login_required
@admin_required
def admin_vehicles_form(request, vehicle_id=None):
    """Form thêm/sửa xe (Admin)"""
    vehicle = None
    teachers = Teacher.get_with_user_info()
    
    # Thêm field 'id' từ '_id' để dùng trong template
    for teacher in teachers:
        teacher['id'] = str(teacher['_id'])
    
    if vehicle_id:
        vehicle_list = Vehicle.get_with_teacher_info(vehicle_id)
        vehicle = vehicle_list[0] if vehicle_list else None
    
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        license_plate = request.POST.get('license_plate')
        vehicle_type = request.POST.get('vehicle_type')
        brand = request.POST.get('brand')
        color = request.POST.get('color')
        
        try:
            if vehicle_id:
                # Update
                Vehicle.update(vehicle_id, {
                    'license_plate': license_plate,
                    'vehicle_type': vehicle_type,
                    'brand': brand,
                    'color': color
                })
                messages.success(request, 'Cập nhật xe thành công')
            else:
                # Create
                new_vehicle_id = Vehicle.create(
                    teacher_id, license_plate, vehicle_type, brand, color
                )
                # Generate QR
                QRCode.generate(str(new_vehicle_id))
                messages.success(request, 'Thêm xe thành công')
            
            return redirect('admin_vehicles_list')
            
        except ValueError as e:
            messages.error(request, str(e))
    
    context = {
        'vehicle': vehicle,
        'teachers': teachers,
        'vehicle_types': Vehicle.VEHICLE_TYPES
    }
    return render(request, 'admin/vehicles_form.html', context)

@login_required
@admin_required
def admin_vehicles_delete(request, vehicle_id):
    """Xóa xe (Admin)"""
    try:
        Vehicle.delete(vehicle_id)
        QRCode.deactivate(vehicle_id)
        messages.success(request, 'Xóa xe thành công')
    except Exception as e:
        messages.error(request, f'Lỗi: {str(e)}')
    
    return redirect('admin_vehicles_list')


# ============ TEACHER VIEWS ============

@login_required
@teacher_required
def teacher_vehicles_list(request):
    """Danh sách xe của tôi (Teacher)"""
    teacher = Teacher.get_by_user_id(request.session['user_id'])
    vehicles = Vehicle.get_by_teacher(str(teacher['_id']))
    
    # Get QR codes và thêm field 'id' từ '_id' để dùng trong template
    for vehicle in vehicles:
        vehicle['id'] = str(vehicle['_id'])
        qr_code = QRCode.get_by_vehicle(str(vehicle['_id']))
        vehicle['qr_code'] = qr_code
    
    context = {
        'vehicles': vehicles
    }
    return render(request, 'teacher/my_vehicles.html', context)

@login_required
@teacher_required
def teacher_vehicles_form(request):
    """Đăng ký xe mới (Teacher)"""
    if request.method == 'POST':
        license_plate = request.POST.get('license_plate')
        vehicle_type = request.POST.get('vehicle_type')
        brand = request.POST.get('brand')
        color = request.POST.get('color')
        
        try:
            teacher = Teacher.get_by_user_id(request.session['user_id'])
            
            # Create vehicle
            new_vehicle_id = Vehicle.create(
                str(teacher['_id']), 
                license_plate, 
                vehicle_type, 
                brand, 
                color
            )
            
            # Generate QR
            QRCode.generate(str(new_vehicle_id))
            
            messages.success(request, 'Đăng ký xe thành công')
            return redirect('teacher_vehicles_list')
            
        except ValueError as e:
            messages.error(request, str(e))
    
    context = {
        'vehicle_types': Vehicle.VEHICLE_TYPES
    }
    return render(request, 'teacher/vehicle_form.html', context)

@login_required
@teacher_required
def teacher_view_qr(request, vehicle_id):
    """Xem QR code (Teacher)"""
    vehicle = Vehicle.get_by_id(vehicle_id)
    
    # Check ownership
    teacher = Teacher.get_by_user_id(request.session['user_id'])
    if str(vehicle['teacher_id']) != str(teacher['_id']):
        messages.error(request, 'Bạn không có quyền xem QR này')
        return redirect('teacher_vehicles_list')
    
    qr_code = QRCode.get_by_vehicle(vehicle_id)
    
    context = {
        'vehicle': vehicle,
        'qr_code': qr_code
    }
    return render(request, 'teacher/my_qr.html', context)


@login_required
@teacher_required
def teacher_parking_history(request, vehicle_id):
    """Xem lịch sử gửi xe của một phương tiện (Teacher)"""
    # Load vehicle and check ownership
    vehicle = Vehicle.get_by_id(vehicle_id)
    if not vehicle:
        messages.error(request, 'Không tìm thấy xe')
        return redirect('teacher_vehicles_list')

    teacher = Teacher.get_by_user_id(request.session['user_id'])
    if str(vehicle['teacher_id']) != str(teacher['_id']):
        messages.error(request, 'Bạn không có quyền xem lịch sử xe này')
        return redirect('teacher_vehicles_list')

    # Fetch history
    history = ParkingHistory.get_by_vehicle(vehicle_id, limit=100)

    context = {
        'vehicle': vehicle,
        'history': history
    }
    return render(request, 'teacher/parking_history.html', context)