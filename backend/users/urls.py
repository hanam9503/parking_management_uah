from django.urls import path
from users import views

urlpatterns = [
    # Auth
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin (custom) Dashboard — renamed to avoid colliding with Django's /admin/
    path('management/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin Teachers CRUD (under /management/ to avoid Django admin namespace)
    path('management/teachers/', views.admin_teachers_list, name='admin_teachers_list'),
    path('management/teachers/add/', views.admin_teachers_form, name='admin_teachers_add'),
    path('management/teachers/edit/<str:teacher_id>/', views.admin_teachers_form, name='admin_teachers_edit'),
    path('management/teachers/delete/<str:teacher_id>/', views.admin_teachers_delete, name='admin_teachers_delete'),
    
    # Admin Parking (custom)
    path('management/parking/history/', views.admin_parking_history, name='admin_parking_history'),
    path('management/parking/config/', views.admin_parking_config, name='admin_parking_config'),
    
    # Security Dashboard
    path('security/dashboard/', views.security_dashboard, name='security_dashboard'),
    path('security/scan/', views.security_scan_qr, name='security_scan_qr'),
    path('security/manual/', views.security_manual_entry, name='security_manual_entry'),
    path('security/checkout/<str:vehicle_id>/', views.security_checkout, name='security_checkout'),
    
    # Teacher Dashboard
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
]