from datetime import datetime
from bson import ObjectId
import bcrypt

def hash_password(password):
    """Hash password với bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def str_to_objectid(id_str):
    """Convert string to ObjectId"""
    try:
        return ObjectId(id_str)
    except:
        return None

def objectid_to_str(obj_id):
    """Convert ObjectId to string"""
    return str(obj_id) if obj_id else None

def get_current_timestamp():
    """Get current timestamp"""
    return datetime.utcnow()