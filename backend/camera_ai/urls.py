from django.urls import path
from camera_ai import views

urlpatterns = [
    path('camera/', views.camera_dashboard, name='camera_dashboard'),
    path('camera/start/', views.start_camera, name='camera_start'),
    path('camera/stop/', views.stop_camera, name='camera_stop'),
    path('camera/feed/', views.video_feed, name='camera_feed'),
    path('camera/api/scan/', views.process_qr_scan, name='camera_api_scan'),
    path('camera/api/test/', views.test_detection, name='camera_api_test'),
]
