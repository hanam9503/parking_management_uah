# camera_ai/service.py
"""
Camera AI Service - Nhận diện biển số xe bằng YOLO + OCR
"""
import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
from datetime import datetime
import os
from pathlib import Path

class CameraAIService:
    """Service xử lý nhận diện biển số xe"""
    
    def __init__(self, model_path=None, camera_id=0):
        """
        Khởi tạo service
        
        Args:
            model_path: Đường dẫn đến model YOLO (tự động tìm nếu None)
            camera_id: ID của camera (0 cho webcam, hoặc RTSP URL)
        """
        # Nếu không chỉ định, tìm model trong thư mục camera_ai/models
        if model_path is None:
            current_dir = Path(__file__).parent
            model_path = current_dir / 'models' / 'license-plate-finetune-v1m.pt'
            model_path = str(model_path)
        
        # Khởi tạo YOLO model
        try:
            # Kiểm tra model có tồn tại không
            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                print(f"[WARNING] Model file not found: {model_path}")
                print(f"[INFO] Camera AI sẽ hoạt động ở chế độ disabled")
                self.model = None
            else:
                self.model = YOLO(model_path)
                print(f"[OK] Model loaded: {model_path}")
        except Exception as e:
            print(f"[ERROR] Không thể load model: {e}")
            print(f"[INFO] Camera AI sẽ hoạt động ở chế độ disabled")
            self.model = None
        
        # Khởi tạo EasyOCR reader (hỗ trợ tiếng Việt)
        try:
            self.reader = easyocr.Reader(['en', 'vi'], gpu=True)
            print("[OK] OCR reader initialized")
        except Exception as e:
            print(f"[WARNING] GPU OCR failed, using CPU: {e}")
            self.reader = easyocr.Reader(['en', 'vi'], gpu=False)
        
        # Camera
        self.camera_id = camera_id
        self.cap = None
        
        # Thư mục lưu ảnh
        self.save_dir = Path('camera_ai/captured_images')
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Confidence threshold
        self.conf_threshold = 0.5
        
    def start_camera(self):
        """Khởi động camera"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise Exception(f"Không thể mở camera: {self.camera_id}")
        return True
    
    def stop_camera(self):
        """Dừng camera"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
    
    def capture_frame(self):
        """Chụp 1 frame từ camera"""
        if not self.cap or not self.cap.isOpened():
            raise Exception("Camera chưa được khởi động")
        
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Không thể đọc frame từ camera")
        
        return frame
    
    def detect_license_plate(self, frame):
        """
        Nhận diện vị trí biển số trong ảnh
        
        Args:
            frame: Ảnh đầu vào (numpy array)
            
        Returns:
            list: Danh sách các bounding box của biển số
        """
        if not self.model:
            return []
        
        # Chạy YOLO detection
        results = self.model(frame, conf=self.conf_threshold)
        
        plates = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Lọc chỉ lấy class "license plate" (class 0 trong custom model)
                # Hoặc dùng class "car" nếu chưa có custom model
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                if conf > self.conf_threshold:
                    # Lấy tọa độ bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    plates.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': conf,
                        'class': cls
                    })
        
        return plates
    
    def extract_text_from_plate(self, frame, bbox):
        """
        Trích xuất text từ vùng biển số (hỗ trợ cả 1 dòng và 2 dòng)
        
        Args:
            frame: Ảnh gốc
            bbox: Bounding box [x1, y1, x2, y2]
            
        Returns:
            str: Text nhận diện được
        """
        x1, y1, x2, y2 = bbox
        
        # Crop vùng biển số
        plate_img = frame[y1:y2, x1:x2]
        
        # Tiền xử lý ảnh
        plate_img = self._preprocess_plate(plate_img)
        
        # OCR với paragraph mode để đọc nhiều dòng
        results = self.reader.readtext(
            plate_img,
            paragraph=False,  # Đọc từng text block
            min_size=10,
            text_threshold=0.7,
            low_text=0.4,
            link_threshold=0.4,
            canvas_size=2560,
            mag_ratio=1.5
        )
        
        if not results:
            return None
        
        # Xử lý biển số 2 dòng
        plate_text, confidence = self._process_multiline_plate(results, plate_img.shape)
        
        if not plate_text:
            return None
        
        # Chuẩn hóa text
        plate_text = self._normalize_plate_text(plate_text)
        
        return {
            'text': plate_text,
            'confidence': confidence
        }
    
    def _process_multiline_plate(self, ocr_results, img_shape):
        """
        Xử lý kết quả OCR cho biển số 1 hoặc 2 dòng
        
        Args:
            ocr_results: Kết quả từ EasyOCR
            img_shape: (height, width) của ảnh
            
        Returns:
            tuple: (text, confidence)
        """
        if not ocr_results:
            return None, 0.0
        
        img_height = img_shape[0]
        
        # Sắp xếp theo tọa độ Y (từ trên xuống dưới)
        sorted_results = sorted(ocr_results, key=lambda x: x[0][0][1])
        
        # Phân tích để xác định biển 1 dòng hay 2 dòng
        lines = self._group_text_by_lines(sorted_results, img_height)
        
        if len(lines) >= 2:
            # Biển 2 dòng
            return self._handle_two_line_plate(lines)
        else:
            # Biển 1 dòng
            return self._handle_one_line_plate(sorted_results)
    
    def _group_text_by_lines(self, ocr_results, img_height):
        """
        Nhóm các text block theo dòng (dựa vào tọa độ Y)
        """
        if not ocr_results:
            return []
        
        # Threshold để xác định 2 text có cùng dòng hay không
        line_threshold = img_height * 0.3
        
        lines = []
        current_line = [ocr_results[0]]
        current_y = ocr_results[0][0][0][1]
        
        for result in ocr_results[1:]:
            y = result[0][0][1]
            
            # Nếu chênh lệch Y nhỏ → cùng dòng
            if abs(y - current_y) < line_threshold:
                current_line.append(result)
            else:
                # Dòng mới
                lines.append(current_line)
                current_line = [result]
                current_y = y
        
        # Thêm dòng cuối
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _handle_two_line_plate(self, lines):
        """
        Xử lý biển số 2 dòng
        Format: 
        - Dòng 1: Mã tỉnh (VD: 29-K1)
        - Dòng 2: Số (VD: 12345)
        """
        if len(lines) < 2:
            return None, 0.0
        
        # Dòng 1: Mã tỉnh
        line1_texts = []
        line1_confs = []
        for result in lines[0]:
            line1_texts.append(result[1])
            line1_confs.append(result[2])
        
        # Dòng 2: Số
        line2_texts = []
        line2_confs = []
        for result in lines[1]:
            line2_texts.append(result[1])
            line2_confs.append(result[2])
        
        # Ghép text
        line1 = ''.join(line1_texts)
        line2 = ''.join(line2_texts)
        
        # Biển số 2 dòng: Ghép với dấu gạch ngang
        plate_text = f"{line1}-{line2}"
        
        # Confidence trung bình
        all_confs = line1_confs + line2_confs
        avg_confidence = sum(all_confs) / len(all_confs) if all_confs else 0.0
        
        return plate_text, avg_confidence
    
    def _handle_one_line_plate(self, ocr_results):
        """
        Xử lý biển số 1 dòng
        Format: 29K1-12345
        """
        # Sắp xếp theo tọa độ X (từ trái sang phải)
        sorted_results = sorted(ocr_results, key=lambda x: x[0][0][0])
        
        # Ghép tất cả text
        texts = [result[1] for result in sorted_results]
        confidences = [result[2] for result in sorted_results]
        
        plate_text = ''.join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return plate_text, avg_confidence
    
    def _preprocess_plate(self, plate_img):
        """Tiền xử lý ảnh biển số để OCR tốt hơn"""
        # Convert to grayscale
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        # Resize để OCR tốt hơn
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _normalize_plate_text(self, text):
        """
        Chuẩn hóa text biển số
        - Loại bỏ khoảng trắng thừa
        - Uppercase
        - Loại bỏ ký tự đặc biệt
        """
        # Uppercase và loại bỏ khoảng trắng
        text = text.upper().replace(' ', '')
        
        # Loại bỏ ký tự không phải chữ/số/dấu gạch
        text = ''.join(c for c in text if c.isalnum() or c == '-')
        
        return text
    
    def save_captured_image(self, frame, plate_text, entry_type='checkin'):
        """
        Lưu ảnh đã chụp
        
        Args:
            frame: Ảnh gốc
            plate_text: Biển số nhận diện được
            entry_type: 'checkin' hoặc 'checkout'
            
        Returns:
            str: Đường dẫn file đã lưu
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{entry_type}_{plate_text}_{timestamp}.jpg"
        filepath = self.save_dir / filename
        
        cv2.imwrite(str(filepath), frame)
        
        return str(filepath)
    
    def process_vehicle_entry(self, qr_plate, entry_type='checkin'):
        """
        Xử lý luồng check-in/check-out với xác minh QR code
        
        Args:
            qr_plate: Biển số từ QR code (format: VEHICLE_ID|LICENSE_PLATE)
            entry_type: 'checkin' hoặc 'checkout'
            
        Returns:
            dict: Kết quả xử lý
        """
        try:
            # Parse QR data để lấy vehicle ID
            try:
                vehicle_id, qr_license_plate = qr_plate.split('|')
                qr_normalized = self._normalize_plate_text(qr_license_plate)
            except (ValueError, IndexError):
                qr_normalized = self._normalize_plate_text(qr_plate)
                vehicle_id = None
            
            # Chụp ảnh
            frame = self.capture_frame()
            
            # Nhận diện biển số
            plates = self.detect_license_plate(frame)
            
            if not plates:
                # Nếu không detect được → chỉ cho phép nếu QR hợp lệ
                return {
                    'success': True,
                    'detected_plate': 'UNDETECTED',
                    'qr_plate': qr_normalized,
                    'match': True,  # Trust QR code
                    'confidence': 0.0,
                    'message': f'⚠️ Không detect được biển số, nhưng QR hợp lệ\nVehicle ID: {vehicle_id}',
                    'camera_failed': True,
                    'image_path': None,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Lấy TOP 3 biển số có confidence cao nhất (smoothing)
            top_plates = sorted(plates, key=lambda x: x['confidence'], reverse=True)[:3]
            detected_plates = []
            
            for plate in top_plates:
                ocr_result = self.extract_text_from_plate(frame, plate['bbox'])
                if ocr_result:
                    detected_plates.append({
                        'text': ocr_result['text'],
                        'confidence': ocr_result['confidence'],
                        'detection_confidence': plate['confidence']
                    })
            
            if not detected_plates:
                return {
                    'success': True,
                    'detected_plate': 'UNDETECTED',
                    'qr_plate': qr_normalized,
                    'match': True,  # Trust QR code
                    'confidence': 0.0,
                    'message': f'⚠️ Không đọc được biển số, nhưng QR hợp lệ\nVehicle ID: {vehicle_id}',
                    'camera_failed': True,
                    'image_path': None,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Lấy biển số có confidence cao nhất
            best_detection = max(detected_plates, key=lambda x: x['confidence'])
            detected_plate = best_detection['text']
            
            # So sánh với QR code
            match = (detected_plate == qr_normalized)
            
            # Nếu không khớp, kiểm tra các biển số khác trong TOP 3
            if not match and len(detected_plates) > 1:
                for alt_plate in detected_plates[1:]:
                    if alt_plate['text'] == qr_normalized:
                        # Tìm thấy khớp ở biển số thứ 2, 3
                        detected_plate = alt_plate['text']
                        best_detection['confidence'] = alt_plate['confidence']
                        match = True
                        break
            
            # Lưu ảnh
            image_path = self.save_captured_image(frame, detected_plate, entry_type)
            
            return {
                'success': True,
                'detected_plate': detected_plate,
                'qr_plate': qr_normalized,
                'match': match,
                'confidence': best_detection['confidence'],
                'detection_confidence': best_detection['detection_confidence'],
                'image_path': image_path,
                'vehicle_id': vehicle_id,
                'all_detections': detected_plates,  # Debug info
                'message': f'✅ Biển số khớp! {detected_plate}' if match else f'❌ Biển số không khớp!\nQR: {qr_normalized}\nCamera: {detected_plate}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Lỗi xử lý: {str(e)}',
                'detected_plate': None,
                'qr_plate': qr_plate,
                'match': False
            }
    
    def visualize_detection(self, frame, plates, detected_text=None):
        """
        Vẽ bounding box và text lên ảnh
        
        Args:
            frame: Ảnh gốc
            plates: Danh sách bounding box
            detected_text: Text đã nhận diện
            
        Returns:
            frame: Ảnh đã vẽ
        """
        for plate in plates:
            x1, y1, x2, y2 = plate['bbox']
            conf = plate['confidence']
            
            # Vẽ bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Vẽ confidence
            label = f"Conf: {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Vẽ text nhận diện được
        if detected_text:
            cv2.putText(frame, f"Plate: {detected_text}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return frame


# Singleton instance
camera_service = CameraAIService()