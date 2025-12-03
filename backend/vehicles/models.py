from django.db import models

# Create your models here.
from core.mongodb import vehicles_collection, qr_codes_collection
from core.utils import str_to_objectid, get_current_timestamp
from bson import ObjectId
import qrcode
from io import BytesIO
import os
from django.conf import settings

class Vehicle:
    """Vehicle model"""
    
    VEHICLE_TYPES = ['motorcycle', 'car', 'bicycle']
    
    @staticmethod
    def create(teacher_id, license_plate, vehicle_type, brand=None, color=None):
        """Tạo xe mới"""
        # Validate vehicle type
        if vehicle_type not in Vehicle.VEHICLE_TYPES:
            raise ValueError(f"Invalid vehicle type. Must be one of: {Vehicle.VEHICLE_TYPES}")
        
        # Normalize license plate (uppercase, remove spaces)
        license_plate = license_plate.upper().replace(' ', '')
        
        # Check license plate exists
        if vehicles_collection.find_one({'license_plate': license_plate}):
            raise ValueError("Biển số xe đã tồn tại")
        
        vehicle_data = {
            'teacher_id': str_to_objectid(teacher_id),
            'license_plate': license_plate,
            'vehicle_type': vehicle_type,
            'brand': brand,
            'color': color,
            'is_active': True,
            'created_at': get_current_timestamp()
        }
        
        result = vehicles_collection.insert_one(vehicle_data)
        return result.inserted_id
    
    @staticmethod
    def get_by_id(vehicle_id):
        """Lấy xe theo ID"""
        return vehicles_collection.find_one({'_id': str_to_objectid(vehicle_id), 'is_active': True})
    
    @staticmethod
    def get_by_license_plate(license_plate):
        """Lấy xe theo biển số"""
        license_plate = license_plate.upper().replace(' ', '')
        return vehicles_collection.find_one({'license_plate': license_plate, 'is_active': True})
    
    @staticmethod
    def get_by_teacher(teacher_id):
        """Lấy xe của giảng viên"""
        return list(vehicles_collection.find({'teacher_id': str_to_objectid(teacher_id), 'is_active': True}))
    
    @staticmethod
    def get_all(vehicle_type=None, is_active=None):
        """Lấy tất cả xe"""
        query = {'is_active': True}  # Mặc định lấy xe còn hoạt động
        if vehicle_type:
            query['vehicle_type'] = vehicle_type
        if is_active is not None:
            query['is_active'] = is_active
        return list(vehicles_collection.find(query))
    
    @staticmethod
    def get_with_teacher_info(vehicle_id=None):
        """Lấy xe kèm thông tin giảng viên"""
        # Luôn filter xe còn hoạt động
        match_stage = {'is_active': True}
        if vehicle_id:
            match_stage['_id'] = str_to_objectid(vehicle_id)
        
        pipeline = [
            {'$match': match_stage},
            {
                '$lookup': {
                    'from': 'teachers',
                    'localField': 'teacher_id',
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
        
        return list(vehicles_collection.aggregate(pipeline))
    
    @staticmethod
    def update(vehicle_id, data):
        """Cập nhật xe"""
        # Normalize license plate if updated
        if 'license_plate' in data:
            data['license_plate'] = data['license_plate'].upper().replace(' ', '')
            
            # Check duplicate
            existing = vehicles_collection.find_one({
                'license_plate': data['license_plate'],
                '_id': {'$ne': str_to_objectid(vehicle_id)}
            })
            if existing:
                raise ValueError("Biển số xe đã tồn tại")
        
        return vehicles_collection.update_one(
            {'_id': str_to_objectid(vehicle_id)},
            {'$set': data}
        )
    
    @staticmethod
    def delete(vehicle_id):
        """Xóa xe (soft delete)"""
        return vehicles_collection.update_one(
            {'_id': str_to_objectid(vehicle_id)},
            {'$set': {'is_active': False}}
        )
    
    @staticmethod
    def count_by_type():
        """Thống kê số xe theo loại"""
        pipeline = [
            {
                '$group': {
                    '_id': '$vehicle_type',
                    'count': {'$sum': 1}
                }
            }
        ]
        return list(vehicles_collection.aggregate(pipeline))


class QRCode:
    """QR Code model"""
    
    @staticmethod
    def generate(vehicle_id):
        """Tạo QR code cho xe"""
        vehicle = Vehicle.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found")
        
        # Check if QR exists
        existing_qr = qr_codes_collection.find_one({'vehicle_id': str_to_objectid(vehicle_id)})
        if existing_qr:
            return existing_qr['_id']
        
        # QR data format: VEHICLE_ID|LICENSE_PLATE
        qr_data = f"{str(vehicle['_id'])}|{vehicle['license_plate']}"
        
        # Generate QR image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to media folder
        qr_folder = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(qr_folder, exist_ok=True)
        
        filename = f"qr_{vehicle['_id']}.png"
        filepath = os.path.join(qr_folder, filename)
        img.save(filepath)
        
        # Save to database
        qr_code_data = {
            'vehicle_id': vehicle['_id'],
            'qr_data': qr_data,
            'qr_image_path': f'qr_codes/{filename}',
            'secret_key': str(ObjectId()),  # Random secret
            'is_active': True,
            'created_at': get_current_timestamp()
        }
        
        result = qr_codes_collection.insert_one(qr_code_data)
        return result.inserted_id
    
    @staticmethod
    def get_by_vehicle(vehicle_id):
        """Lấy QR code theo xe"""
        return qr_codes_collection.find_one({'vehicle_id': str_to_objectid(vehicle_id)})
    
    @staticmethod
    def verify(qr_data):
        """Xác thực QR code"""
        qr_code = qr_codes_collection.find_one({'qr_data': qr_data})
        if not qr_code or not qr_code.get('is_active'):
            return None
        
        # Get vehicle info
        vehicle = Vehicle.get_by_id(str(qr_code['vehicle_id']))
        return vehicle
    
    @staticmethod
    def deactivate(vehicle_id):
        """Vô hiệu hóa QR code"""
        return qr_codes_collection.update_one(
            {'vehicle_id': str_to_objectid(vehicle_id)},
            {'$set': {'is_active': False}}
        )