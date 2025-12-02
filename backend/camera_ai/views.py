# camera_ai/views.py
"""
Views cho Camera AI
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from users.decorators import login_required, security_required
from camera_ai.service import camera_service
from parking.models import ParkingHistory
from vehicles.models import Vehicle, QRCode
import cv2
import json

@login_required
@security_required
def camera_dashboard(request):
    """Dashboard quản lý camera"""
    context = {
        'camera_status': 'active' if camera_service.cap and camera_service.cap.isOpened() else 'inactive'
    }
    return render(request, 'camera_ai/dashboard.html', context)

@login_required
@security_required
def start_camera(request):
    """Khởi động camera"""
    try:
        camera_service.start_camera()
        messages.success(request, 'Camera đã được khởi động')
    except Exception as e:
        messages.error(request, f'Lỗi khởi động camera: {str(e)}')
    
    return redirect('camera_dashboard')

@login_required
@security_required
def stop_camera(request):
    """Dừng camera"""
    try:
        camera_service.stop_camera()
        messages.success(request, 'Camera đã được dừng')
    except Exception as e:
        messages.error(request, f'Lỗi dừng camera: {str(e)}')
    
    return redirect('camera_dashboard')

def generate_frames():
    """Generator để stream video"""
    while True:
        try:
            if not camera_service.cap or not camera_service.cap.isOpened():
                break
            
            frame = camera_service.capture_frame()
            
            # Detect plates
            plates = camera_service.detect_license_plate(frame)
            
            # Visualize
            if plates:
                frame = camera_service.visualize_detection(frame, plates)
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Error in frame generation: {e}")
            break

@login_required
@security_required
def video_feed(request):
    """Stream video từ camera"""
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@csrf_exempt
@login_required
@security_required
def process_qr_scan(request):
    """
    API xử lý quét QR code và so sánh với camera
    
    Request body:
    {
        "qr_data": "VEHICLE_ID|LICENSE_PLATE",
        "entry_type": "checkin" hoặc "checkout"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        qr_data = data.get('qr_data')
        entry_type = data.get('entry_type', 'checkin')
        
        if not qr_data:
            return JsonResponse({'error': 'QR data is required'}, status=400)
        
        # Parse QR data
        try:
            vehicle_id, qr_plate = qr_data.split('|')
        except ValueError:
            return JsonResponse({'error': 'Invalid QR format'}, status=400)
        
        # Verify QR code
        vehicle = QRCode.verify(qr_data)
        if not vehicle:
            return JsonResponse({
                'success': False,
                'message': 'QR code không hợp lệ hoặc đã bị vô hiệu hóa'
            }, status=400)
        
        # Process with camera
        result = camera_service.process_vehicle_entry(qr_plate, entry_type)
        
        if not result['success']:
            return JsonResponse(result, status=400)
        
        # Nếu biển số khớp
        if result['match']:
            security_id = request.session.get('user_id')
            
            try:
                if entry_type == 'checkin':
                    # Check-in
                    ParkingHistory.checkin(
                        vehicle_id=vehicle_id,
                        detected_plate=result['detected_plate'],
                        security_id=security_id,
                        qr_license_plate=qr_plate
                    )
                    result['message'] = f"✅ Check-in thành công! Xe {result['detected_plate']}"
                    
                elif entry_type == 'checkout':
                    # Check-out
                    ParkingHistory.checkout(
                        vehicle_id=vehicle_id,
                        security_id=security_id,
                        notes=f"Camera AI verified: {result['detected_plate']}"
                    )
                    result['message'] = f"✅ Check-out thành công! Xe {result['detected_plate']}"
                
                result['vehicle_info'] = {
                    'id': str(vehicle['_id']),
                    'license_plate': vehicle['license_plate'],
                    'vehicle_type': vehicle['vehicle_type']
                }
                
            except ValueError as e:
                result['success'] = False
                result['message'] = str(e)
                return JsonResponse(result, status=400)
        else:
            result['message'] = f"❌ Biển số không khớp!\nQR: {result['qr_plate']}\nCamera: {result['detected_plate']}"
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@security_required
def test_detection(request):
    """Test nhận diện biển số"""
    try:
        frame = camera_service.capture_frame()
        plates = camera_service.detect_license_plate(frame)
        
        results = []
        for plate in plates:
            ocr_result = camera_service.extract_text_from_plate(frame, plate['bbox'])
            if ocr_result:
                results.append({
                    'text': ocr_result['text'],
                    'confidence': ocr_result['confidence'],
                    'bbox': plate['bbox']
                })
        
        return JsonResponse({
            'success': True,
            'plates': results,
            'total': len(results)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
