import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from core.mongodb import db

def init_mongodb():
    """Khởi tạo MongoDB collections và indexes"""
    print("🚀 Initializing MongoDB...")
    
    # Create collections
    collections = [
        'users',
        'teachers',
        'vehicles',
        'qr_codes',
        'parking_history',
        'parking_config',
        'faculty_stats'
    ]
    
    for collection_name in collections:
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            print(f"✅ Created collection: {collection_name}")
        else:
            print(f"ℹ️  Collection already exists: {collection_name}")
    
    # Create indexes
    print("\n📑 Creating indexes...")
    
    # Users indexes
    db.users.create_index('username', unique=True)
    db.users.create_index('email', unique=True)
    db.users.create_index('role')
    print("✅ Users indexes created")
    
    # Teachers indexes
    db.teachers.create_index('user_id', unique=True)
    db.teachers.create_index('employee_id', unique=True)
    db.teachers.create_index('faculty')
    print("✅ Teachers indexes created")
    
    print("\n✅ MongoDB initialization completed!")

if __name__ == '__main__':
    init_mongodb()