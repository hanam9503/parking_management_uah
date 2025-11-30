from django.urls import path
from vehicles import views

urlpatterns = [
    # Admin routes
    path('management/vehicles/', views.admin_vehicles_list, name='admin_vehicles_list'),
    path('management/vehicles/add/', views.admin_vehicles_form, name='admin_vehicles_add'),
    path('management/vehicles/edit/<str:vehicle_id>/', views.admin_vehicles_form, name='admin_vehicles_edit'),
    path('management/vehicles/delete/<str:vehicle_id>/', views.admin_vehicles_delete, name='admin_vehicles_delete'),
    
    # Teacher routes
    path('teacher/vehicles/', views.teacher_vehicles_list, name='teacher_vehicles_list'),
    path('teacher/vehicles/add/', views.teacher_vehicles_form, name='teacher_vehicles_add'),
    path('teacher/vehicles/qr/<str:vehicle_id>/', views.teacher_view_qr, name='teacher_view_qr'),
    path('teacher/vehicles/history/<str:vehicle_id>/', views.teacher_parking_history, name='teacher_parking_history'),
]