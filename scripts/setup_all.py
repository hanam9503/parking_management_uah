#!/usr/bin/env python
"""
Setup script - Chạy tất cả các bước khởi tạo
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

def print_header(text):
    """In header đẹp"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def run_step(step_name, func):
    """Chạy một bước và bắt lỗi"""
    print(f"🔄 {step_name}...")
    try:
        func()
        print(f"✅ {step_name} - DONE\n")
        return True
    except Exception as e:
        print(f"❌ {step_name} - FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def step1_test_connection():
    """Step 1: Test MongoDB connection"""
    from core.mongodb import db
    db.client.admin.command('ping')
    print(f"   Connected to: {db.name}")

def step2_init_mongodb():
    """Step 2: Initialize collections and indexes"""
    from core.mongodb import db
    
    collections = ['users', 'teachers', 'vehicles', 'qr_codes', 
                   'parking_history', 'parking_config', 'faculty_stats']
    
    for col_name in collections:
        if col_name not in db.list_collection_names():
            db.create_collection(col_name)
            print(f"   Created: {col_name}")
    
    # Create indexes
    db.users.create_index('username', unique=True)
    db.users.create_index('email', unique=True)
    db.teachers.create_index('user_id', unique=True)
    db.teachers.create_index('employee_id', unique=True)
    print("   Indexes created")

def step3_seed_users():
    """Step 3: Seed demo users"""
    from users.models import User, Teacher
    from core.mongodb import users_collection, teachers_collection
    
    # Check if already seeded
    if users_collection.count_documents({}) > 0:
        print("   Users already exist, skipping...")
        return
    
    users_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@uah.edu.vn',
            'full_name': 'Nguyễn Văn Admin',
            'phone': '0901234567',
            'role': 'admin'
        },
        {
            'username': 'security',
            'password': 'security123',
            'email': 'security@uah.edu.vn',
            'full_name': 'Trần Văn Bảo Vệ',
            'phone': '0902234567',
            'role': 'security'
        },
        {
            'username': 'teacher1',
            'password': 'teacher123',
            'email': 'nguyenvana@uah.edu.vn',
            'full_name': 'Nguyễn Văn A',
            'phone': '0903234567',
            'role': 'teacher',
            'teacher_info': {
                'employee_id': 'KT001',
                'faculty': 'Khoa Kiến trúc',
                'department': 'Bộ môn Thiết kế Kiến trúc',
                'specialized_area': 'Thiết kế đô thị'
            }
        },
        {
            'username': 'teacher2',
            'password': 'teacher123',
            'email': 'tranthib@uah.edu.vn',
            'full_name': 'Trần Thị B',
            'phone': '0904234567',
            'role': 'teacher',
            'teacher_info': {
                'employee_id': 'XD001',
                'faculty': 'Khoa Xây dựng',
                'department': 'Bộ môn Kết cấu',
                'specialized_area': 'Kết cấu bê tông'
            }
        }
    ]
    
    for user_data in users_data:
        teacher_info = user_data.pop('teacher_info', None)
        user_id = User.create(**user_data)
        print(f"   Created user: {user_data['username']}")
        
        if teacher_info:
            Teacher.create(str(user_id), **teacher_info)
            print(f"     + Teacher profile created")

def step4_init_parking_config():
    """Step 4: Initialize parking config"""
    from parking.models import ParkingConfig
    ParkingConfig.init_default()
    
    configs = ParkingConfig.get_all()
    print("   Parking configs:")
    for config in configs:
        print(f"     - {config['vehicle_type']}: 0/{config['total_capacity']}")

def step5_init_university():
    """Step 5: Initialize university config"""
    from university.models import UniversityConfig
    config = UniversityConfig.get_config()
    print(f"   University: {config['name']}")
    print(f"   Faculties: {len(config['faculties'])}")

def main():
    """Main setup function"""
    print_header("🚀 PARKING MANAGEMENT SYSTEM - FULL SETUP")
    
    steps = [
        ("Step 1: Test MongoDB Connection", step1_test_connection),
        ("Step 2: Initialize Collections & Indexes", step2_init_mongodb),
        ("Step 3: Seed Demo Users", step3_seed_users),
        ("Step 4: Initialize Parking Config", step4_init_parking_config),
        ("Step 5: Initialize University Config", step5_init_university),
    ]
    
    results = []
    for step_name, step_func in steps:
        result = run_step(step_name, step_func)
        results.append((step_name, result))
    
    # Summary
    print_header("📊 SETUP SUMMARY")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for step_name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{status:15} - {step_name}")
    
    print(f"\n🎯 Completed: {success_count}/{total_count} steps")
    
    if success_count == total_count:
        print("\n✨ ALL STEPS COMPLETED SUCCESSFULLY!")
        print("\n📝 Next steps:")
        print("   1. cd backend")
        print("   2. python manage.py runserver")
        print("   3. Open http://localhost:8000/login/")
        print("   4. Login with: admin / admin123")
        print("\n🎉 Happy coding!")
    else:
        print("\n⚠️  Some steps failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)