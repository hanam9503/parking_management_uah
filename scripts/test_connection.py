import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from core.mongodb import db

def test_connection():
    """Test kết nối MongoDB Atlas"""
    print("🧪 Testing MongoDB Atlas connection...")
    
    try:
        # Test ping
        db.client.admin.command('ping')
        print("✅ Ping successful!")
        
        # List databases
        print(f"\n📚 Available databases:")
        for db_name in db.client.list_database_names():
            print(f"   - {db_name}")
        
        # List collections in current database
        print(f"\n📁 Collections in '{db.name}':")
        collections = db.list_collection_names()
        if collections:
            for col in collections:
                count = db[col].count_documents({})
                print(f"   - {col}: {count} documents")
        else:
            print("   (empty)")
        
        # Test insert
        print("\n✍️  Testing insert...")
        result = db.test_collection.insert_one({'test': 'Hello MongoDB Atlas!'})
        print(f"✅ Inserted document with ID: {result.inserted_id}")
        
        # Test find
        doc = db.test_collection.find_one({'test': 'Hello MongoDB Atlas!'})
        print(f"✅ Found document: {doc}")
        
        # Clean up
        db.test_collection.delete_one({'_id': result.inserted_id})
        print("✅ Test document deleted")
        
        print("\n🎉 MongoDB Atlas connection test PASSED!")
        
    except Exception as e:
        print(f"\n❌ Connection test FAILED: {e}")
        raise

if __name__ == '__main__':
    test_connection()