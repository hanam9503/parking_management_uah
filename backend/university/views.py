from django.shortcuts import render, redirect
from django.contrib import messages
from users.decorators import login_required, admin_required
from university.models import FacultyStats, UniversityConfig, SystemStats

@login_required
@admin_required
def faculty_stats_list(request):
    """Danh sách thống kê các khoa"""
    try:
        all_stats = FacultyStats.get_all_stats()
        comparison = FacultyStats.get_comparison_stats()
        system_overview = SystemStats.get_overview()
        
        context = {
            'all_stats': all_stats,
            'comparison': comparison,
            'system_overview': system_overview
        }
        return render(request, 'admin/faculty_stats.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi tải thống kê: {str(e)}')
        return redirect('admin_dashboard')

@login_required
@admin_required
def faculty_stats_detail(request, faculty_name):
    """Thống kê chi tiết một khoa"""
    try:
        stats = FacultyStats.get_faculty_stats(faculty_name)
        top_users = FacultyStats.get_top_users(faculty_name, limit=10)
        
        context = {
            'stats': stats,
            'top_users': top_users,
            'faculty_name': faculty_name
        }
        return render(request, 'admin/faculty_detail.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi tải chi tiết: {str(e)}')
        return redirect('admin_faculty_stats')

@login_required
@admin_required
def system_stats(request):
    """Thống kê tổng hợp hệ thống"""
    try:
        overview = SystemStats.get_overview()
        monthly_stats = SystemStats.get_monthly_stats()
        peak_hours = SystemStats.get_peak_hours()
        
        context = {
            'overview': overview,
            'monthly_stats': monthly_stats,
            'peak_hours': peak_hours
        }
        return render(request, 'admin/system_stats.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi tải thống kê hệ thống: {str(e)}')
        return redirect('admin_dashboard')