from django.db import models

# Create your models here.
from core.mongodb import parking_history_collection, parking_config_collection
from core.utils import str_to_objectid, get_current_timestamp
from datetime import datetime

class ParkingConfig:
    """Cấu hình bãi xe"""
    
    @staticmethod
    def init_default():
        """Khởi tạo cấu hình mặc định"""
        configs = [
            {'vehicle_type': 'motorcycle', 'total_capacity': 150, 'current_occupied': 0},
            {'vehicle_type': 'car', 'total_capacity': 50, 'current_occupied': 0},
            {'vehicle_type': 'bicycle', 'total_capacity': 100, 'current_occupied': 0}
        ]
        
        for config in configs:
            if not parking_config_collection.find_one({'vehicle_type': config['vehicle_type']}):
                config['created_at'] = get_current_timestamp()
                parking_config_collection.insert_one(config)
    
    @staticmethod
    def get_by_type(vehicle_type):
        """Lấy cấu hình theo loại xe"""
        return parking_config_collection.find_one({'vehicle_type': vehicle_type})
    
    @staticmethod
    def get_all():
        """Lấy tất cả cấu hình"""
        return list(parking_config_collection.find())
    
    @staticmethod
    def update_occupied(vehicle_type, increment=1):
        """Cập nhật số xe đang đỗ"""
        return parking_config_collection.update_one(
            {'vehicle_type': vehicle_type},
            {'$inc': {'current_occupied': increment}}
        )
    
    @staticmethod
    def update_capacity(vehicle_type, new_capacity):
        """Cập nhật sức chứa"""
        return parking_config_collection.update_one(
            {'vehicle_type': vehicle_type},
            {'$set': {'total_capacity': new_capacity}}
        )


class ParkingHistory:
    """Lịch sử ra vào"""
    
    @staticmethod
    def checkin(vehicle_id, detected_plate, security_id=None, qr_license_plate=None):
        """Check-in xe"""
        # Check if vehicle already inside
        existing = parking_history_collection.find_one({
            'vehicle_id': str_to_objectid(vehicle_id),
            'status': 'inside'
        })
        
        if existing:
            raise ValueError("Xe đang trong bãi")
        
        from vehicles.models import Vehicle
        vehicle = Vehicle.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found")
        
        # Create history record
        history_data = {
            'vehicle_id': str_to_objectid(vehicle_id),
            'security_id': str_to_objectid(security_id) if security_id else None,
            'time_in': get_current_timestamp(),
            'time_out': None,
            'detected_plate': detected_plate,
            'qr_license_plate': qr_license_plate,
            'status': 'inside',
            'notes': None
        }
        
        result = parking_history_collection.insert_one(history_data)
        
        # Update parking config
        ParkingConfig.update_occupied(vehicle['vehicle_type'], 1)
        
        return result.inserted_id
    
    @staticmethod
    def checkout(vehicle_id, security_id=None, notes=None):
        """Check-out xe"""
        # Find current parking record
        history = parking_history_collection.find_one({
            'vehicle_id': str_to_objectid(vehicle_id),
            'status': 'inside'
        })
        
        if not history:
            raise ValueError("Xe không trong bãi")
        
        from vehicles.models import Vehicle
        vehicle = Vehicle.get_by_id(vehicle_id)
        
        # Update history
        update_data = {
            'time_out': get_current_timestamp(),
            'status': 'completed'
        }
        
        if notes:
            update_data['notes'] = notes
        
        parking_history_collection.update_one(
            {'_id': history['_id']},
            {'$set': update_data}
        )
        
        # Update parking config
        ParkingConfig.update_occupied(vehicle['vehicle_type'], -1)
        
        return history['_id']
    
    @staticmethod
    def get_current_parking():
        """Lấy xe đang trong bãi"""
        pipeline = [
            {'$match': {'status': 'inside'}},
            {
                '$lookup': {
                    'from': 'vehicles',
                    'localField': 'vehicle_id',
                    'foreignField': '_id',
                    'as': 'vehicle'
                }
            },
            {'$unwind': '$vehicle'},
            {
                '$lookup': {
                    'from': 'teachers',
                    'localField': 'vehicle.teacher_id',
                    'foreignField': '_id',
                    'as': 'teacher'
                }
            },
            {'$unwind': '$teacher'},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'teacher.user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {'$unwind': '$user'}
        ]
        
        return list(parking_history_collection.aggregate(pipeline))
    
    @staticmethod
    def get_by_vehicle(vehicle_id, limit=10):
        """Lấy lịch sử của xe"""
        return list(parking_history_collection.find(
            {'vehicle_id': str_to_objectid(vehicle_id)}
        ).sort('time_in', -1).limit(limit))
    
    @staticmethod
    def get_today():
        """Lấy lịch sử hôm nay"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return list(parking_history_collection.find({
            'time_in': {'$gte': today_start}
        }).sort('time_in', -1))
    
    @staticmethod
    def get_statistics():
        """Thống kê tổng quan"""
        total_today = len(ParkingHistory.get_today())
        current_inside = parking_history_collection.count_documents({'status': 'inside'})
        
        return {
            'total_today': total_today,
            'current_inside': current_inside
        }