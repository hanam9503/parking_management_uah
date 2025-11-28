from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv('MONGODB_URI'))
class MongoDB:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def connect(self):
        """Kết nối MongoDB Atlas"""
        try:
            # Connection string từ .env
            uri = os.getenv('MONGODB_URI')
            
            # Kết nối với MongoDB Atlas
            self._client = MongoClient(
                uri,
                server_api=ServerApi('1'),
                # Timeout settings
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            self._client.admin.command('ping')
            print("✅ Pinged MongoDB Atlas. Connected successfully!")
            
            # Get database
            db_name = os.getenv('MONGODB_DB', 'parkingDBsql')
            self._db = self._client[db_name]
            
            print(f"✅ Using database: {db_name}")
            return self._db
            
        except Exception as e:
            print(f"❌ MongoDB Atlas connection error: {e}")
            raise

    def get_db(self):
        """Lấy database instance"""
        if self._db is None:
            self.connect()
        return self._db

    def get_collection(self, collection_name):
        """Lấy collection"""
        return self.get_db()[collection_name]
    
    def disconnect(self):
        """Ngắt kết nối"""
        if self._client:
            self._client.close()
            print("✅ MongoDB Atlas disconnected")

# Singleton instance
mongodb = MongoDB()
db = mongodb.get_db()

# Collections
users_collection = db['users']
teachers_collection = db['teachers']
vehicles_collection = db['vehicles']
qr_codes_collection = db['qr_codes']
parking_history_collection = db['parking_history']
parking_config_collection = db['parking_config']
faculty_stats_collection = db['faculty_stats']