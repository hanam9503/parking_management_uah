import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')
django.setup()

from users.models import User, Teacher
from core.mongodb import users_collection, teachers_collection
from core.utils import str_to_objectid

# Tìm user teacher1
user = users_collection.find_one({'username': 'teacher1'})
user_id_str = str(user['_id'])
user_id_obj = user['_id']

print('User ID (string):', user_id_str)
print('User ID (ObjectId):', user_id_obj)
print()

# Kiểm tra cách chuyển đổi
user_id_converted = str_to_objectid(user_id_str)
print('User ID converted:', user_id_converted)
print('Type:', type(user_id_converted))
print()

# Tìm teacher với cách chuyển đổi
teacher1 = teachers_collection.find_one({'user_id': user_id_converted})
print('Teacher found with converted ID:', teacher1 is not None)
print()

# Tìm teacher với ID trực tiếp
teacher2 = teachers_collection.find_one({'user_id': user_id_obj})
print('Teacher found with direct ID:', teacher2 is not None)
print()

# Chi tiết
if teacher1:
    print('Details from teacher1:', teacher1['_id'])
if teacher2:
    print('Details from teacher2:', teacher2['_id'])

# Kiểm tra bằng hàm get_by_user_id
result = Teacher.get_by_user_id(user_id_str)
print('Result from Teacher.get_by_user_id:', result is not None)
