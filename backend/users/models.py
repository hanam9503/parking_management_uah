from core.mongodb import users_collection, teachers_collection
from core.utils import hash_password, verify_password, str_to_objectid, get_current_timestamp
from bson import ObjectId

class User:
    """User model"""
    
    ROLES = ['admin', 'security', 'teacher']
    
    @staticmethod
    def create(username, password, email, full_name, phone, role):
        """Tạo user mới"""
        # Validate role
        if role not in User.ROLES:
            raise ValueError(f"Invalid role. Must be one of: {User.ROLES}")
        
        # Check username exists
        if users_collection.find_one({'username': username}):
            raise ValueError("Username already exists")
        
        # Check email exists
        if users_collection.find_one({'email': email}):
            raise ValueError("Email already exists")
        
        user_data = {
            'username': username,
            'password_hash': hash_password(password),
            'email': email,
            'full_name': full_name,
            'phone': phone,
            'role': role,
            'is_active': True,
            'created_at': get_current_timestamp(),
            'last_login': None
        }
        
        result = users_collection.insert_one(user_data)
        return result.inserted_id
    
    @staticmethod
    def authenticate(username, password):
        """Xác thực user"""
        user = users_collection.find_one({'username': username})
        
        if not user:
            return None
        
        if not user.get('is_active'):
            return None
        
        if verify_password(password, user['password_hash']):
            # Update last login
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'last_login': get_current_timestamp()}}
            )
            return user
        
        return None
    
    @staticmethod
    def get_by_id(user_id):
        """Lấy user theo ID"""
        return users_collection.find_one({'_id': str_to_objectid(user_id)})
    
    @staticmethod
    def get_by_username(username):
        """Lấy user theo username"""
        return users_collection.find_one({'username': username})
    
    @staticmethod
    def get_all(role=None):
        """Lấy tất cả users"""
        query = {}
        if role:
            query['role'] = role
        return list(users_collection.find(query))
    
    @staticmethod
    def update(user_id, data):
        """Cập nhật user"""
        return users_collection.update_one(
            {'_id': str_to_objectid(user_id)},
            {'$set': data}
        )
    
    @staticmethod
    def delete(user_id):
        """Xóa user (soft delete)"""
        return users_collection.update_one(
            {'_id': str_to_objectid(user_id)},
            {'$set': {'is_active': False}}
        )


class Teacher:
    """Teacher model"""
    
    @staticmethod
    def create(user_id, employee_id, faculty, department, specialized_area=None):
        """Tạo teacher profile"""
        # Check employee_id exists
        if teachers_collection.find_one({'employee_id': employee_id}):
            raise ValueError("Employee ID already exists")
        
        teacher_data = {
            'user_id': str_to_objectid(user_id),
            'employee_id': employee_id,
            'faculty': faculty,
            'department': department,
            'specialized_area': specialized_area,
            'created_at': get_current_timestamp()
        }
        
        result = teachers_collection.insert_one(teacher_data)
        return result.inserted_id
    
    @staticmethod
    def get_by_user_id(user_id):
        """Lấy teacher theo user_id"""
        return teachers_collection.find_one({'user_id': str_to_objectid(user_id)})
    
    @staticmethod
    def get_by_id(teacher_id):
        """Lấy teacher theo ID"""
        return teachers_collection.find_one({'_id': str_to_objectid(teacher_id)})
    
    @staticmethod
    def get_by_employee_id(employee_id):
        """Lấy teacher theo mã nhân viên"""
        return teachers_collection.find_one({'employee_id': employee_id})
    
    @staticmethod
    def get_all(faculty=None):
        """Lấy tất cả teachers"""
        query = {}
        if faculty:
            query['faculty'] = faculty
        return list(teachers_collection.find(query))
    
    @staticmethod
    def get_with_user_info(teacher_id=None):
        """Lấy teacher kèm thông tin user"""
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {'$unwind': '$user'}
        ]
        
        if teacher_id:
            pipeline.insert(0, {'$match': {'_id': str_to_objectid(teacher_id)}})
        
        return list(teachers_collection.aggregate(pipeline))
    
    @staticmethod
    def update(teacher_id, data):
        """Cập nhật teacher"""
        return teachers_collection.update_one(
            {'_id': str_to_objectid(teacher_id)},
            {'$set': data}
        )
    
    @staticmethod
    def delete(teacher_id):
        """Xóa teacher"""
        return teachers_collection.delete_one({'_id': str_to_objectid(teacher_id)})