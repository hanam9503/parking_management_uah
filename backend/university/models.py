from core.mongodb import db, teachers_collection, vehicles_collection, parking_history_collection
from core.utils import get_current_timestamp
from datetime import datetime, timedelta
from collections import defaultdict

class UniversityConfig:
    """Cấu hình trường đại học"""
    
    @staticmethod
    def get_config():
        """Lấy cấu hình trường"""
        config = db.university_config.find_one({})
        if not config:
            # Tạo config mặc định
            default_config = {
                'name': 'Trường Đại học Kiến trúc Hà Nội',
                'address': 'Km 10, Đường Nguyễn Trãi, Quận Thanh Xuân, TP Hà Nội',
                'faculties': [
                    'Khoa Kiến trúc',
                    'Khoa Xây dựng',
                    'Khoa Quy hoạch',
                    'Khoa Nội thất',
                    'Khoa Kỹ thuật công trình'
                ],
                'created_at': get_current_timestamp()
            }
            db.university_config.insert_one(default_config)
            return default_config
        return config
    
    @staticmethod
    def get_faculties():
        """Lấy danh sách khoa"""
        config = UniversityConfig.get_config()
        return config.get('faculties', [])


class FacultyStats:
    """Thống kê theo khoa"""
    
    @staticmethod
    def get_all_stats():
        """Lấy thống kê tất cả khoa"""
        faculties = UniversityConfig.get_faculties()
        stats = []
        
        for faculty in faculties:
            stats.append(FacultyStats.get_faculty_stats(faculty))
        
        return stats
    
    @staticmethod
    def get_faculty_stats(faculty_name):
        """Lấy thống kê chi tiết một khoa"""
        # Đếm giảng viên
        total_teachers = teachers_collection.count_documents({'faculty': faculty_name})
        
        # Lấy danh sách teacher_ids của khoa
        teacher_ids = [t['_id'] for t in teachers_collection.find(
            {'faculty': faculty_name}, 
            {'_id': 1}
        )]
        
        # Đếm xe
        total_vehicles = vehicles_collection.count_documents({
            'teacher_id': {'$in': teacher_ids}
        })
        
        # Đếm xe theo loại
        vehicle_pipeline = [
            {'$match': {'teacher_id': {'$in': teacher_ids}}},
            {'$group': {
                '_id': '$vehicle_type',
                'count': {'$sum': 1}
            }}
        ]
        vehicle_by_type = list(vehicles_collection.aggregate(vehicle_pipeline))
        vehicle_types = {item['_id']: item['count'] for item in vehicle_by_type}
        
        # Đếm xe đang trong bãi
        vehicles_in_parking = FacultyStats._count_vehicles_in_parking(teacher_ids)
        
        # Thống kê lượt ra vào hôm nay
        today_entries = FacultyStats._count_today_entries(teacher_ids)
        
        # Thống kê 7 ngày
        weekly_stats = FacultyStats._get_weekly_stats(teacher_ids)
        
        return {
            'faculty_name': faculty_name,
            'total_teachers': total_teachers,
            'total_vehicles': total_vehicles,
            'vehicle_types': {
                'motorcycle': vehicle_types.get('motorcycle', 0),
                'car': vehicle_types.get('car', 0),
                'bicycle': vehicle_types.get('bicycle', 0)
            },
            'vehicles_in_parking': vehicles_in_parking,
            'today_entries': today_entries,
            'weekly_stats': weekly_stats
        }
    
    @staticmethod
    def _count_vehicles_in_parking(teacher_ids):
        """Đếm xe đang trong bãi của khoa"""
        # Lấy vehicle_ids
        vehicle_ids = [v['_id'] for v in vehicles_collection.find(
            {'teacher_id': {'$in': teacher_ids}},
            {'_id': 1}
        )]
        
        return parking_history_collection.count_documents({
            'vehicle_id': {'$in': vehicle_ids},
            'status': 'inside'
        })
    
    @staticmethod
    def _count_today_entries(teacher_ids):
        """Đếm lượt vào hôm nay"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        vehicle_ids = [v['_id'] for v in vehicles_collection.find(
            {'teacher_id': {'$in': teacher_ids}},
            {'_id': 1}
        )]
        
        return parking_history_collection.count_documents({
            'vehicle_id': {'$in': vehicle_ids},
            'time_in': {'$gte': today_start}
        })
    
    @staticmethod
    def _get_weekly_stats(teacher_ids):
        """Thống kê 7 ngày gần nhất"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=6)
        
        vehicle_ids = [v['_id'] for v in vehicles_collection.find(
            {'teacher_id': {'$in': teacher_ids}},
            {'_id': 1}
        )]
        
        # Aggregate by day
        pipeline = [
            {
                '$match': {
                    'vehicle_id': {'$in': vehicle_ids},
                    'time_in': {'$gte': week_ago}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$time_in'
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        results = list(parking_history_collection.aggregate(pipeline))
        
        # Fill missing days with 0
        stats_dict = {item['_id']: item['count'] for item in results}
        weekly_data = []
        
        for i in range(7):
            date = today - timedelta(days=6-i)
            date_str = date.strftime('%Y-%m-%d')
            weekly_data.append({
                'date': date_str,
                'day': date.strftime('%d/%m'),
                'count': stats_dict.get(date_str, 0)
            })
        
        return weekly_data
    
    @staticmethod
    def get_comparison_stats():
        """So sánh giữa các khoa"""
        all_stats = FacultyStats.get_all_stats()
        
        return {
            'by_teachers': sorted(all_stats, key=lambda x: x['total_teachers'], reverse=True),
            'by_vehicles': sorted(all_stats, key=lambda x: x['total_vehicles'], reverse=True),
            'by_parking': sorted(all_stats, key=lambda x: x['vehicles_in_parking'], reverse=True),
            'by_today': sorted(all_stats, key=lambda x: x['today_entries'], reverse=True)
        }
    
    @staticmethod
    def get_top_users(faculty_name=None, limit=10):
        """Top giảng viên sử dụng bãi xe nhiều nhất"""
        query = {}
        if faculty_name:
            query['faculty'] = faculty_name
        
        # Lấy teacher_ids
        teacher_ids = [t['_id'] for t in teachers_collection.find(query, {'_id': 1})]
        
        # Aggregate parking history
        pipeline = [
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
                '$match': {
                    'vehicle.teacher_id': {'$in': teacher_ids}
                }
            },
            {
                '$group': {
                    '_id': '$vehicle.teacher_id',
                    'total_entries': {'$sum': 1}
                }
            },
            {'$sort': {'total_entries': -1}},
            {'$limit': limit},
            {
                '$lookup': {
                    'from': 'teachers',
                    'localField': '_id',
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


class SystemStats:
    """Thống kê tổng hợp hệ thống"""
    
    @staticmethod
    def get_overview():
        """Tổng quan hệ thống"""
        total_teachers = teachers_collection.count_documents({})
        total_vehicles = vehicles_collection.count_documents({})
        
        # Vehicles by type
        vehicle_pipeline = [
            {'$group': {
                '_id': '$vehicle_type',
                'count': {'$sum': 1}
            }}
        ]
        vehicle_stats = list(vehicles_collection.aggregate(vehicle_pipeline))
        vehicles_by_type = {item['_id']: item['count'] for item in vehicle_stats}
        
        # Current parking
        current_inside = parking_history_collection.count_documents({'status': 'inside'})
        
        # Today entries
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_entries = parking_history_collection.count_documents({
            'time_in': {'$gte': today_start}
        })
        
        # Total entries
        total_entries = parking_history_collection.count_documents({})
        
        return {
            'total_teachers': total_teachers,
            'total_vehicles': total_vehicles,
            'vehicles_by_type': vehicles_by_type,
            'current_inside': current_inside,
            'today_entries': today_entries,
            'total_entries': total_entries
        }
    
    @staticmethod
    def get_monthly_stats():
        """Thống kê theo tháng"""
        # Last 6 months
        today = datetime.now()
        six_months_ago = today - timedelta(days=180)
        
        pipeline = [
            {
                '$match': {
                    'time_in': {'$gte': six_months_ago}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m',
                            'date': '$time_in'
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        results = list(parking_history_collection.aggregate(pipeline))
        return results
    
    @staticmethod
    def get_peak_hours():
        """Giờ cao điểm"""
        pipeline = [
            {
                '$group': {
                    '_id': {
                        '$hour': '$time_in'
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        results = list(parking_history_collection.aggregate(pipeline))
        return results