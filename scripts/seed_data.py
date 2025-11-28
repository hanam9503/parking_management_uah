# scripts/seed_users_mongodb.py
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')  # nhớ thêm dòng này

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from core.mongodb import db
from bson import ObjectId


def get_teacher_data(username):
    """Lấy data teacher theo username"""
    teachers = {
        'teacher1': {
            'employee_id': 'KT001',
            'faculty': 'Khoa Kiến trúc',
            'department': 'Bộ môn Thiết kế Kiến trúc',
            'specialized_area': 'Thiết kế đô thị'
        },
        'teacher2': {
            'employee_id': 'XD001',
            'faculty': 'Khoa Xây dựng',
            'department': 'Bộ môn Kết cấu',
            'specialized_area': 'Kết cấu bê tông'
        },
        'teacher3': {
            'employee_id': 'NT001',
            'faculty': 'Khoa Nội thất',
            'department': 'Bộ môn Thiết kế Nội thất',
            'specialized_area': 'Thiết kế nội thất dân dụng'
        }
    }
    return teachers.get(username, {})


def seed_users():
    """Tạo dữ liệu user mẫu vào MongoDB"""
    print("Seeding users into MongoDB...")

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
            'role': 'teacher'
        },
        {
            'username': 'teacher2',
            'password': 'teacher123',
            'email': 'tranthib@uah.edu.vn',
            'full_name': 'Trần Thị B',
            'phone': '0904234567',
            'role': 'teacher'
        },
        {
            'username': 'teacher3',
            'password': 'teacher123',
            'email': 'levanthic@uah.edu.vn',
            'full_name': 'Lê Văn C',
            'phone': '0905234567',
            'role': 'teacher'
        }
    ]

    for user_data in users_data:
        try:
            existing_user = db.users.find_one({"username": user_data['username']})

            if not existing_user:
                result = db.users.insert_one(user_data)
                user_id = result.inserted_id
                print(f"Created user: {user_data['username']}")
            else:
                user_id = existing_user["_id"]
                print(f"User exists: {user_data['username']}")

            # Nếu là teacher thì tạo bản ghi teachers
            if user_data['role'] == 'teacher':
                teacher_defaults = get_teacher_data(user_data['username'])

                existing_teacher = db.teachers.find_one({"user_id": user_id})

                teacher_payload = {
                    "user_id": user_id,
                    **teacher_defaults
                }

                if not existing_teacher:
                    db.teachers.insert_one(teacher_payload)
                    print(f"  Created teacher profile for: {user_data['username']}")
                else:
                    print(f"  Teacher profile exists for: {user_data['username']}")

        except Exception as e:
            print(f"Error creating user {user_data['username']}: {e}")


if __name__ == '__main__':
    seed_users()
    print("\n✅ Seeding completed!")
