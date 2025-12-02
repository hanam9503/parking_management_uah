# camera_ai/simulation_views.py
"""
Views cho Simulated Camera System
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from users.decorators import login_required, admin_required, security_required
from camera_ai.simulation import simulated_camera_service
import cv2
import numpy as np
import json
from pathlib import Path
from django.conf import settings

# ============================================
# ADMIN VIEWS - Camera Control
# ============================================

@login_required
@admin_required
def admin_camera_control(request):
    """Admin Dashboard - Điều khiển 2 camera"""
    status = simulated_camera_service.get_status()
    
    # Get available videos
    video_folder_1 = Path(settings.MEDIA_ROOT) / 'camera_simulations' / 'videos' / 'checkin'
    video_folder_2 = Path(settings.MEDIA_ROOT) / 'camera_simulations' / 'videos' / 'checkout'
    image_folder = Path(settings.MEDIA_ROOT) / 'camera_simulations' / 'images'
    
    videos_checkin = [f.name for f in video_folder_1.glob('*.mp4')] if video_folder_1.exists() else []
    videos_checkout = [f.name for f in video_folder_2.glob('*.mp4')] if video_folder_2.exists() else []
    images = []
    if image_folder.exists():
        images.extend([f.name for f in image_folder.glob('*.jpg')])
        images.extend([f.name for f in image_folder.glob('*.jpeg')])
        images.extend([f.name for f in image_folder.glob('*.png')])
    
    context = {
        'status': status,
        'videos_checkin': videos_checkin,
        'videos_checkout': videos_checkout,
        'images': images
    }
    return render(request, 'camera_ai/admin_control.html', context)


@login_required
@admin_required
def admin_upload_video(request):
    """Upload video cho camera"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    camera_type = request.POST.get('camera_type')  # 'checkin' or 'checkout'
    video_file = request.FILES.get('video')
    
    if not video_file:
        return JsonResponse({'error': 'No video file'}, status=400)
    
    if camera_type not in ['checkin', 'checkout']:
        return JsonResponse({'error': 'Invalid camera type'}, status=400)
    
    # Save file
    save_path = f'camera_simulations/videos/{camera_type}/{video_file.name}'
    filename = default_storage.save(save_path, video_file)
    
    messages.success(request, f'Video uploaded: {video_file.name}')
    return JsonResponse({
        'success': True,
        'filename': video_file.name
    })


@login_required
@admin_required
def admin_upload_image(request):
    """Upload ảnh để inject"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    image_file = request.FILES.get('image')
    
    if not image_file:
        return JsonResponse({'error': 'No image file'}, status=400)
    
    # Validate file type
    allowed_ext = ['.jpg', '.jpeg', '.png']
    file_ext = Path(image_file.name).suffix.lower()
    
    if file_ext not in allowed_ext:
        return JsonResponse({
            'error': f'Invalid file type. Allowed: {allowed_ext}'
        }, status=400)
    
    try:
        # Save file
        save_path = f'camera_simulations/images/{image_file.name}'
        filename = default_storage.save(save_path, image_file)
        
        messages.success(request, f'Image uploaded: {image_file.name}')
        return JsonResponse({
            'success': True,
            'filename': image_file.name
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=400)


# ============================================
# API ENDPOINTS - Camera Control
# ============================================

@csrf_exempt
@login_required
@admin_required
def api_camera_start(request):
    """API: Khởi động camera"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        camera_id = data.get('camera_id')
        video_filename = data.get('video_filename')
        
        simulated_camera_service.start_camera(camera_id, video_filename)
        
        return JsonResponse({
            'success': True,
            'message': f'Camera {camera_id} started',
            'status': simulated_camera_service.get_status()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@login_required
@admin_required
def api_camera_stop(request):
    """API: Dừng camera"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        camera_id = data.get('camera_id')
        
        simulated_camera_service.stop_camera(camera_id)
        
        return JsonResponse({
            'success': True,
            'message': f'Camera {camera_id} stopped',
            'status': simulated_camera_service.get_status()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@login_required
@admin_required
def api_inject_image(request):
    """API: Chèn ảnh vào camera"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        camera_id = data.get('camera_id')
        image_filename = data.get('image_filename')
        duration = float(data.get('duration', 5.0))
        
        simulated_camera_service.inject_image(camera_id, image_filename, duration)
        
        return JsonResponse({
            'success': True,
            'message': f'Image injected to {camera_id}',
            'camera_id': camera_id,
            'image': image_filename,
            'duration': duration
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def api_camera_status(request):
    """API: Lấy trạng thái cameras"""
    status = simulated_camera_service.get_status()
    return JsonResponse({
        'success': True,
        'status': status
    })


# ============================================
# STREAMING ENDPOINTS
# ============================================

def generate_camera_stream(camera_id):
    """Generator để stream video từ camera"""
    while True:
        try:
            if not simulated_camera_service.is_camera_active(camera_id):
                # Return placeholder frame
                placeholder = cv2.imread(str(Path(__file__).parent / 'static' / 'camera_offline.png'))
                if placeholder is None:
                    # Create black frame with text
                    placeholder = 255 * np.ones((480, 640, 3), dtype=np.uint8)
                    cv2.putText(placeholder, 'Camera Offline', (200, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                ret, buffer = cv2.imencode('.jpg', placeholder)
            else:
                # Get frame with detection
                result = simulated_camera_service.get_frame_with_detection(camera_id)
                
                if result['success'] and result['frame'] is not None:
                    ret, buffer = cv2.imencode('.jpg', result['frame'])
                else:
                    continue
            
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
        except Exception as e:
            print(f"Stream error [{camera_id}]: {e}")
            break


@login_required
def stream_camera_1(request):
    """Stream camera 1 (Check-in)"""
    return StreamingHttpResponse(
        generate_camera_stream('camera_1'),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


@login_required
def stream_camera_2(request):
    """Stream camera 2 (Check-out)"""
    return StreamingHttpResponse(
        generate_camera_stream('camera_2'),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


# ============================================
# FRAME CAPTURE ENDPOINTS - For static preview
# ============================================

@login_required
def capture_camera_frame(request, camera_id):
    """Capture a single JPEG frame from camera for preview"""
    try:
        result = simulated_camera_service.get_frame_with_detection(camera_id)
        
        if result['success'] and result['frame'] is not None:
            ret, buffer = cv2.imencode('.jpg', result['frame'])
            if ret:
                return HttpResponse(buffer.tobytes(), content_type='image/jpeg')
        
        # Return placeholder if offline
        placeholder_path = Path(__file__).parent / 'static' / 'camera_offline.png'
        if placeholder_path.exists():
            with open(str(placeholder_path), 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
        
        # Return black frame
        black_frame = 0 * np.ones((480, 640, 3), dtype=np.uint8)
        ret, buffer = cv2.imencode('.jpg', black_frame)
        return HttpResponse(buffer.tobytes(), content_type='image/jpeg')
        
    except Exception as e:
        print(f"Frame capture error [{camera_id}]: {e}")
        black_frame = 0 * np.ones((480, 640, 3), dtype=np.uint8)
        ret, buffer = cv2.imencode('.jpg', black_frame)
        return HttpResponse(buffer.tobytes(), content_type='image/jpeg')


# ============================================
# SECURITY VIEWS - Live View
# ============================================

@login_required
@security_required
def security_live_view(request):
    """Security Dashboard - Xem live 2 camera"""
    status = simulated_camera_service.get_status()
    
    context = {
        'status': status
    }
    return render(request, 'camera_ai/security_live_view.html', context)