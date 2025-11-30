import sys
import os
sys.stdout.reconfigure(encoding='utf-8')     

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from university.models import FacultyStats, UniversityConfig, SystemStats

def test_stats():
    """Test các chức năng thống kê"""
    print("🧪 Testing Faculty Statistics...")
    print("=" * 60)
    
    # Test 1: Get all faculties
    print("\n1️⃣ Testing UniversityConfig.get_faculties()")
    faculties = UniversityConfig.get_faculties()
    print(f"✓ Found {len(faculties)} faculties:")
    for faculty in faculties:
        print(f"  - {faculty}")
    
    # Test 2: Get all stats
    print("\n2️⃣ Testing FacultyStats.get_all_stats()")
    all_stats = FacultyStats.get_all_stats()
    print(f"✓ Generated stats for {len(all_stats)} faculties")
    for stat in all_stats:
        print(f"\n  📊 {stat['faculty_name']}:")
        print(f"     - Giảng viên: {stat['total_teachers']}")
        print(f"     - Xe đăng ký: {stat['total_vehicles']}")
        print(f"     - Trong bãi: {stat['vehicles_in_parking']}")
        print(f"     - Lượt hôm nay: {stat['today_entries']}")
    
    # Test 3: Get specific faculty stats
    if faculties:
        test_faculty = faculties[0]
        print(f"\n3️⃣ Testing FacultyStats.get_faculty_stats('{test_faculty}')")
        stats = FacultyStats.get_faculty_stats(test_faculty)
        print(f"✓ Detailed stats for {test_faculty}:")
        print(f"  - Vehicle types:")
        print(f"    • Xe máy: {stats['vehicle_types']['motorcycle']}")
        print(f"    • Ô tô: {stats['vehicle_types']['car']}")
        print(f"    • Xe đạp: {stats['vehicle_types']['bicycle']}")
        print(f"  - Weekly stats ({len(stats['weekly_stats'])} days):")
        for day in stats['weekly_stats']:
            print(f"    • {day['day']}: {day['count']} lượt")
    
    # Test 4: Get comparison stats
    print("\n4️⃣ Testing FacultyStats.get_comparison_stats()")
    comparison = FacultyStats.get_comparison_stats()
    print("✓ Top 3 khoa có nhiều GV nhất:")
    for i, stat in enumerate(comparison['by_teachers'][:3], 1):
        print(f"  {i}. {stat['faculty_name']}: {stat['total_teachers']} GV")
    
    # Test 5: Get top users
    print("\n5️⃣ Testing FacultyStats.get_top_users()")
    top_users = FacultyStats.get_top_users(limit=5)
    print(f"✓ Top 5 giảng viên sử dụng nhiều nhất:")
    for i, user in enumerate(top_users[:5], 1):
        print(f"  {i}. {user['user']['full_name']}: {user['total_entries']} lượt")
    
    # Test 6: System overview
    print("\n6️⃣ Testing SystemStats.get_overview()")
    overview = SystemStats.get_overview()
    print("✓ System overview:")
    print(f"  - Tổng GV: {overview['total_teachers']}")
    print(f"  - Tổng xe: {overview['total_vehicles']}")
    print(f"  - Trong bãi: {overview['current_inside']}")
    print(f"  - Lượt hôm nay: {overview['today_entries']}")
    print(f"  - Tổng lượt: {overview['total_entries']}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")

if __name__ == '__main__':
    try:
        test_stats()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()