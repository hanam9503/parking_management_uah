import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')
django.setup()

from users.models import Teacher
from vehicles.models import Vehicle
from parking.models import ParkingHistory
from core.utils import str_to_objectid

# Dữ liệu test
user_id = '692869dc8b20e9539f57ad22'

# Test 1: get_by_user_id
print("=" * 50)
print("Test 1: Teacher.get_by_user_id")
try:
    teacher = Teacher.get_by_user_id(user_id)
    if teacher:
        teacher_id = str(teacher['_id'])
        print(f"✓ Teacher found: {teacher_id}")
        
        # Test 2: Vehicle.get_by_teacher
        print("=" * 50)
        print("Test 2: Vehicle.get_by_teacher")
        try:
            vehicles = Vehicle.get_by_teacher(teacher_id)
            print(f"✓ Vehicles found: {len(vehicles)} vehicles")
            
            if vehicles:
                # Test 3: QRCode.get_by_vehicle
                print("=" * 50)
                print("Test 3: QRCode.get_by_vehicle")
                for i, vehicle in enumerate(vehicles[:1]):
                    try:
                        from vehicles.models import QRCode
                        vehicle_id = str(vehicle['_id'])
                        qr = QRCode.get_by_vehicle(vehicle_id)
                        print(f"✓ Vehicle {i}: {vehicle_id} - QR found: {qr is not None}")
                    except Exception as e:
                        print(f"✗ Vehicle {i}: Error - {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                # Test 4: ParkingHistory.get_by_vehicle
                print("=" * 50)
                print("Test 4: ParkingHistory.get_by_vehicle")
                for i, vehicle in enumerate(vehicles[:1]):
                    try:
                        vehicle_id = str(vehicle['_id'])
                        history = ParkingHistory.get_by_vehicle(vehicle_id, limit=5)
                        print(f"✓ Vehicle {i}: {vehicle_id} - History found: {len(history) if history else 0} records")
                    except Exception as e:
                        print(f"✗ Vehicle {i}: Error - {str(e)}")
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"✗ Teacher not found")
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("=" * 50)
print("All tests completed")
