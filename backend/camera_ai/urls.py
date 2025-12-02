from django.urls import path
from camera_ai import views, simulation_views

urlpatterns = [
    # Original camera routes (keep existing)
    path('camera/', views.camera_dashboard, name='camera_dashboard'),
    path('camera/start/', views.start_camera, name='camera_start'),
    path('camera/stop/', views.stop_camera, name='camera_stop'),
    path('camera/feed/', views.video_feed, name='camera_feed'),
    path('camera/api/scan/', views.process_qr_scan, name='camera_api_scan'),
    path('camera/api/test/', views.test_detection, name='camera_api_test'),
    
    # ============================================
    # SIMULATED CAMERA SYSTEM - NEW ROUTES
    # ============================================
    
    # Admin - Camera Control
    path('simulation/admin/control/', simulation_views.admin_camera_control, name='admin_camera_control'),
    path('simulation/admin/upload-video/', simulation_views.admin_upload_video, name='admin_upload_video'),
    path('simulation/admin/upload-image/', simulation_views.admin_upload_image, name='admin_upload_image'),
    
    # API - Camera Control
    path('simulation/api/camera/start/', simulation_views.api_camera_start, name='api_camera_start'),
    path('simulation/api/camera/stop/', simulation_views.api_camera_stop, name='api_camera_stop'),
    path('simulation/api/inject/', simulation_views.api_inject_image, name='api_inject_image'),
    path('simulation/api/status/', simulation_views.api_camera_status, name='api_camera_status'),
    
    # Streaming
    path('simulation/stream/camera1/', simulation_views.stream_camera_1, name='stream_camera_1'),
    path('simulation/stream/camera2/', simulation_views.stream_camera_2, name='stream_camera_2'),
    
    # Frame capture for preview
    path('simulation/frame/<str:camera_id>/', simulation_views.capture_camera_frame, name='capture_camera_frame'),
    
    # Security - Live View
    path('simulation/security/live/', simulation_views.security_live_view, name='security_live_view'),
]