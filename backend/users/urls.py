from django.urls import path
from users import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('security/dashboard/', views.security_dashboard, name='security_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
]