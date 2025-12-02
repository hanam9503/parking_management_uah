#!/usr/bin/env python
"""
Demo Full System - Tạo dữ liệu demo đầy đủ cho presentation
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from users.models import User, Teacher
from vehicles.models import Vehicle, QRCode
from parking.models import ParkingHistory, ParkingConfig
from datetime import datetime, timedelta
import random

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def demo_step_1():
    """Tạo thêm giảng viên"""
    print("🎭 Tạo thêm giảng viên demo...")
    
    teachers_data = [
        {
            'username': 'teacher4',
            'password': 'teacher123',
            'email': 'phamvand@uah.edu.vn',
            'full_name': 'Phạm Văn D',
            'phone': '0906234567',
            'role': 'teacher',
            'employee_id': 'QH001',
            'faculty': 'Khoa Quy hoạch',
            'department': 'Bộ môn Quy hoạch đô thị',
            'specialized_area': 'Quy hoạch giao thông'
        },
        {
            'username': 'teacher5',
            'password': 'teacher123',
            'email': 'hoangthie@uah.edu.vn',
            'full_name': 'Hoàng Thị E',
            'phone': '0907234567',
            'role': 'teacher',
            'employee_id': 'KTC001',
            'faculty': 'Khoa Kỹ thuật công trình',
            'department': 'Bộ môn Nền móng',
            'specialized_area': 'Địa kỹ thuật'
        }
    ]
    
    for data in teachers_data:
        try:
            if not User.get_by_username(data['username']):
                teacher_info = {
                    'employee_id': data.pop('employee_id'),
                    'faculty': data.pop('faculty'),
                    'department': data.pop('department'),
                    'specialized_area': data.pop('specialized_area')
                }
                
                user_id = User.create(**data)
                Teacher.create(str(user_id), **teacher_info)
                print(f"  ✓ Created: {data['full_name']}")
            else:
                print(f"  - Already exists: {data['full_name']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

def demo_step_2():
    """Đăng ký xe cho mỗi giảng viên"""
    print("\n🚗 Đăng ký xe cho giảng viên...")
    
    # Get all teachers
    teachers = Teacher.get_all()
    
    vehicles_data = [
        {'license_plate': '29K1-12345', 'type': 'motorcycle', 'brand': 'Honda Wave', 'color': 'Đỏ'},
        {'license_plate': '30A-67890', 'type': 'car', 'brand': 'Toyota Vios', 'color': 'Trắng'},
        {'license_plate': '29B2-11111', 'type': 'motorcycle', 'brand': 'Yamaha Exciter', 'color': 'Đen'},
        {'license_plate': '30C-22222', 'type': 'motorcycle', 'brand': 'Honda Air Blade', 'color': 'Xanh'},
        {'license_plate': '29K9-33333', 'type': 'bicycle', 'brand': 'Giant', 'color': 'Đỏ'},
    ]
    
    for i, teacher in enumerate(teachers[:5]):
        if i < len(vehicles_data):
            vehicle_data = vehicles_data[i]
            try:
                # Check if already exists
                if not Vehicle.get_by_license_plate(vehicle_data['license_plate']):
                    vehicle_id = Vehicle.create(
                        str(teacher['_id']),
                        vehicle_data['license_plate'],
                        vehicle_data['type'],
                        vehicle_data['brand'],
                        vehicle_data['color']
                    )
                    
                    # Generate QR code
                    QRCode.generate(str(vehicle_id))
                    
                    print(f"  ✓ Registered: {vehicle_data['license_plate']} for {teacher['user']['full_name'] if 'user' in teacher else 'teacher'}")
                else:
                    print(f"  - Already exists: {vehicle_data['license_plate']}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

def demo_step_3():
    """Tạo lịch sử check-in/out"""
    print("\n📊 Tạo lịch sử check-in/out...")
    
    vehicles = Vehicle.get_all()
    
    # Create some parking history
    for vehicle in vehicles[:3]:
        try:
            # Check-in today
            vehicle_id = str(vehicle['_id'])
            
            # Check if already checked in
            from core.mongodb import parking_history_collection
            existing = parking_history_collection.find_one({
                'vehicle_id': vehicle['_id'],
                'status': 'inside'
            })
            
            if not existing:
                ParkingHistory.checkin(
                    vehicle_id,
                    detected_plate=vehicle['license_plate'],
                    qr_license_plate=vehicle['license_plate']
                )
                print(f"  ✓ Checked-in: {vehicle['license_plate']}")
            else:
                print(f"  - Already inside: {vehicle['license_plate']}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Create completed entries for yesterday
    yesterday = datetime.now() - timedelta(days=1)
    for vehicle in vehicles:
        try:
            from core.mongodb import parking_history_collection
            
            # Create manual entry for demo
            history_data = {
                'vehicle_id': vehicle['_id'],
                'security_id': None,
                'time_in': yesterday.replace(hour=8, minute=random.randint(0, 59)),
                'time_out': yesterday.replace(hour=17, minute=random.randint(0, 59)),
                'detected_plate': vehicle['license_plate'],
                'qr_license_plate': vehicle['license_plate'],
                'status': 'completed',
                'notes': None
            }
            
            # Check if entry exists
            exists = parking_history_collection.find_one({
                'vehicle_id': vehicle['_id'],
                'time_in': {'$gte': yesterday.replace(hour=0, minute=0)},
                'time_in': {'$lt': yesterday.replace(hour=23, minute=59)}
            })
            
            if not exists:
                parking_history_collection.insert_one(history_data)
                print(f"  ✓ Created history: {vehicle['license_plate']} (yesterday)")
                
        except Exception as e:
            print(f"  ✗ Error creating history: {e}")

def demo_step_4():
    """Hiển thị thống kê"""
    print("\n📈 Thống kê hệ thống:")
    
    from university.models import SystemStats
    
    overview = SystemStats.get_overview()
    
    print(f"""
    📊 TỔNG QUAN
    ├─ Giảng viên: {overview['total_teachers']}
    ├─ Tổng xe: {overview['total_vehicles']}
    ├─ Đang trong bãi: {overview['current_inside']}
    ├─ Lượt hôm nay: {overview['today_entries']}
    └─ Tổng lượt: {overview['total_entries']}
    
    🚗 PHÂN LOẠI XE
    ├─ Xe máy: {overview['vehicles_by_type'].get('motorcycle', 0)}
    ├─ Ô tô: {overview['vehicles_by_type'].get('car', 0)}
    └─ Xe đạp: {overview['vehicles_by_type'].get('bicycle', 0)}
    """)
    
    # Faculty stats
    from university.models import FacultyStats
    all_stats = FacultyStats.get_all_stats()
    
    print("    🏢 THỐNG KÊ THEO KHOA")
    for stat in all_stats:
        if stat['total_teachers'] > 0:
            print(f"    ├─ {stat['faculty_name']}")
            print(f"    │  ├─ GV: {stat['total_teachers']}, Xe: {stat['total_vehicles']}")
            print(f"    │  └─ Trong bãi: {stat['vehicles_in_parking']}, Hôm nay: {stat['today_entries']}")

def demo_step_5():
    """In thông tin đăng nhập"""
    print("\n🔐 THÔNG TIN ĐĂNG NHẬP:")
    
    accounts = [
        ('admin', 'admin123', 'Quản trị viên'),
        ('security', 'security123', 'Bảo vệ'),
        ('teacher1', 'teacher123', 'Giảng viên 1'),
        ('teacher2', 'teacher123', 'Giảng viên 2'),
        ('teacher3', 'teacher123', 'Giảng viên 3'),
    ]
    
    print("\n    ╔═══════════════════════════════════════════╗")
    print("    ║         TÀI KHOẢN DEMO                    ║")
    print("    ╠═══════════════════════════════════════════╣")
    for username, password, role in accounts:
        print(f"    ║ {username:15} │ {password:12} │ {role:15} ║")
    print("    ╚═══════════════════════════════════════════╝")

def main():
    print_header("🚀 DEMO FULL SYSTEM - PARKING MANAGEMENT")
    
    try:
        demo_step_1()
        demo_step_2()
        demo_step_3()
        demo_step_4()
        demo_step_5()
        
        print_header("✅ DEMO DATA CREATED SUCCESSFULLY!")
        
        print("""
🎉 HỆ THỐNG SẴN SÀNG CHO DEMO!

📝 NEXT STEPS:
   1. cd backend
   2. python manage.py runserver
   3. Mở http://localhost:8000/login/
   4. Đăng nhập với các tài khoản ở trên
   5. Khám phá các tính năng

🎯 DEMO SCENARIOS:
   ✓ Admin: Quản lý GV, xe, xem thống kê
   ✓ Security: Check-in/out, quét QR, nhập thủ công
   ✓ Teacher: Xem xe, QR code, lịch sử

💡 FEATURES:
   ✓ Dashboard với real-time stats
   ✓ Quản lý giảng viên & xe
   ✓ QR Code generation
   ✓ Parking history
   ✓ Faculty statistics
   ✓ Beautiful UI with Tailwind CSS

🎊 GOOD LUCK WITH YOUR PRESENTATION!
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)