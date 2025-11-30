from django.urls import path
from university import views

urlpatterns = [
    # Faculty Stats
    path('management/stats/faculty/', views.faculty_stats_list, name='admin_faculty_stats'),
    path('management/stats/faculty/<str:faculty_name>/', views.faculty_stats_detail, name='admin_faculty_detail'),
    
    # System Stats
    path('management/stats/system/', views.system_stats, name='admin_system_stats'),
]