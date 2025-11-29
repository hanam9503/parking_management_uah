import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')
django.setup()

from users.models import User
from core.mongodb import users_collection

# Tìm user teacher1 và lấy thông tin đủ
user = users_collection.find_one({'username': 'teacher1'})
print('User found:', user is not None)
print('User role:', user.get('role'))
print('User is_active:', user.get('is_active'))
print()

# Giả lập session
session = {
    'user_id': str(user['_id']),
    'username': user['username'],
    'full_name': user['full_name'],
    'role': user['role']
}
print('Session:', session)
print()

# Kiểm tra decorator logic
user_role = session.get('role')
print('User role from session:', user_role)
print('Is teacher?:', user_role == 'teacher')
print('Is in roles list:', user_role in ['teacher'])
