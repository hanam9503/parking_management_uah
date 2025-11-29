import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from parking.models import ParkingConfig

def init_parking_config():
    """Khởi tạo cấu hình bãi xe mặc định"""
    print("🚀 Initializing parking configuration...")
    
    try:
        ParkingConfig.init_default()
        print("✅ Parking configuration initialized successfully!")
        
        # Display configs
        configs = ParkingConfig.get_all()
        print("\n📊 Current parking configuration:")
        for config in configs:
            print(f"  - {config['vehicle_type']}: {config['current_occupied']}/{config['total_capacity']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    init_parking_config()