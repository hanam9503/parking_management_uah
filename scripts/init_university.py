import sys
import os
sys.stdout.reconfigure(encoding='utf-8')     

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from university.models import UniversityConfig

def init_university():
    """Khởi tạo cấu hình trường"""
    print("🚀 Initializing university configuration...")
    
    try:
        config = UniversityConfig.get_config()
        print("✅ University configuration initialized successfully!")
        print(f"\n📚 University: {config['name']}")
        print(f"📍 Address: {config['address']}")
        print(f"\n🏢 Faculties ({len(config['faculties'])}):")
        for faculty in config['faculties']:
            print(f"  - {faculty}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    init_university()