# camera_ai/simulation.py
"""
Simulated Camera Service - Mô phỏng 2 camera với khả năng inject ảnh
"""
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import threading
import time
from queue import Queue
from typing import Optional, Dict, Any
from django.conf import settings

class SimulatedCamera:
    """Class đại diện cho 1 camera ảo"""
    
    def __init__(self, camera_id: str, camera_type: str):
        """
        Args:
            camera_id: "camera_1" hoặc "camera_2"
            camera_type: "checkin" hoặc "checkout"
        """
        self.camera_id = camera_id
        self.camera_type = camera_type
        self.is_active = False
        self.current_video = None
        self.cap = None
        self.injection_queue = Queue()
        self.injection_active = False
        self.injection_duration = 0
        self.injection_start = 0
        
        # Folders
        self.video_folder = Path(settings.MEDIA_ROOT) / 'camera_simulations' / 'videos' / camera_type
        self.video_folder.mkdir(parents=True, exist_ok=True)
        
        # Thread
        self.frame_thread = None
        self.running = False
        self.latest_frame = None
        self.frame_lock = threading.Lock()
    
    def start(self, video_path: Optional[str] = None):
        """Khởi động camera"""
        if video_path:
            self.current_video = video_path
        
        if not self.current_video:
            raise ValueError(f"No video set for {self.camera_id}")
        
        # Open video
        video_full_path = self.video_folder / self.current_video
        self.cap = cv2.VideoCapture(str(video_full_path))
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_full_path}")
        
        self.is_active = True
        self.running = True
        
        # Start frame generation thread
        self.frame_thread = threading.Thread(target=self._generate_frames, daemon=True)
        self.frame_thread.start()
        
        print(f"[{self.camera_id}] Started with video: {self.current_video}")
    
    def stop(self):
        """Dừng camera"""
        self.is_active = False
        self.running = False
        
        if self.frame_thread:
            self.frame_thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        print(f"[{self.camera_id}] Stopped")
    
    def inject_image(self, image_path: str, duration: float = 5.0):
        """
        Chèn ảnh vào stream trong khoảng thời gian
        
        Args:
            image_path: Đường dẫn đến ảnh
            duration: Thời gian hiển thị ảnh (giây)
        """
        img_full_path = Path(settings.MEDIA_ROOT) / 'camera_simulations' / 'images' / image_path
        
        if not img_full_path.exists():
            raise FileNotFoundError(f"Image not found: {img_full_path}")
        
        # Read image
        injected_frame = cv2.imread(str(img_full_path))
        
        if injected_frame is None:
            raise ValueError(f"Cannot read image: {img_full_path}")
        
        # Add to queue
        self.injection_queue.put({
            'frame': injected_frame,
            'duration': duration,
            'timestamp': time.time()
        })
        
        print(f"[{self.camera_id}] Image injected: {image_path} for {duration}s")
    
    def _generate_frames(self):
        """Thread để generate frames liên tục"""
        fps = 30  # Target FPS
        frame_delay = 1.0 / fps
        
        while self.running:
            start_time = time.time()
            
            # Check injection queue
            if not self.injection_queue.empty() and not self.injection_active:
                injection_data = self.injection_queue.get()
                self.injection_active = True
                self.injection_duration = injection_data['duration']
                self.injection_start = time.time()
                
                with self.frame_lock:
                    self.latest_frame = injection_data['frame'].copy()
            
            # If injection active, continue showing injected frame
            elif self.injection_active:
                elapsed = time.time() - self.injection_start
                if elapsed >= self.injection_duration:
                    self.injection_active = False
                # Frame already set, just wait
            
            # Normal video frame
            else:
                ret, frame = self.cap.read()
                
                if not ret:
                    # Loop video
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                
                if ret:
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
            
            # Maintain FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_delay - elapsed)
            time.sleep(sleep_time)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Lấy frame hiện tại"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None


class SimulatedCameraService:
    """Service quản lý 2 camera mô phỏng"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.camera_1 = SimulatedCamera("camera_1", "checkin")
        self.camera_2 = SimulatedCamera("camera_2", "checkout")
        
        # Load AI service for detection
        from camera_ai.service import camera_service
        self.ai_service = camera_service
        
        self._initialized = True
        print("[SimulatedCameraService] Initialized")
    
    def start_camera(self, camera_id: str, video_filename: Optional[str] = None):
        """Khởi động camera"""
        camera = self._get_camera(camera_id)
        camera.start(video_filename)
    
    def stop_camera(self, camera_id: str):
        """Dừng camera"""
        camera = self._get_camera(camera_id)
        camera.stop()
    
    def inject_image(self, camera_id: str, image_filename: str, duration: float = 5.0):
        """Chèn ảnh vào camera"""
        camera = self._get_camera(camera_id)
        camera.inject_image(image_filename, duration)
    
    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Lấy frame từ camera"""
        camera = self._get_camera(camera_id)
        return camera.get_frame()
    
    def get_frame_with_detection(self, camera_id: str) -> Dict[str, Any]:
        """Lấy frame và chạy detection"""
        frame = self.get_frame(camera_id)
        
        if frame is None:
            return {
                'success': False,
                'message': 'Camera not active',
                'frame': None
            }
        
        # Run YOLO detection
        plates = self.ai_service.detect_license_plate(frame)
        
        detected_plate = None
        confidence = 0.0
        
        if plates:
            best_plate = max(plates, key=lambda x: x['confidence'])
            ocr_result = self.ai_service.extract_text_from_plate(frame, best_plate['bbox'])
            
            if ocr_result:
                detected_plate = ocr_result['text']
                confidence = ocr_result['confidence']
                
                # Draw visualization
                frame = self.ai_service.visualize_detection(
                    frame, 
                    [best_plate], 
                    detected_plate
                )
        
        return {
            'success': True,
            'frame': frame,
            'detected_plate': detected_plate,
            'confidence': confidence,
            'camera_id': camera_id
        }
    
    def is_camera_active(self, camera_id: str) -> bool:
        """Kiểm tra camera có đang chạy không"""
        camera = self._get_camera(camera_id)
        return camera.is_active
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái toàn bộ hệ thống"""
        return {
            'camera_1': {
                'id': 'camera_1',
                'type': 'checkin',
                'active': self.camera_1.is_active,
                'current_video': self.camera_1.current_video,
                'injection_active': self.camera_1.injection_active
            },
            'camera_2': {
                'id': 'camera_2',
                'type': 'checkout',
                'active': self.camera_2.is_active,
                'current_video': self.camera_2.current_video,
                'injection_active': self.camera_2.injection_active
            }
        }
    
    def _get_camera(self, camera_id: str) -> SimulatedCamera:
        """Helper để lấy camera object"""
        if camera_id == "camera_1":
            return self.camera_1
        elif camera_id == "camera_2":
            return self.camera_2
        else:
            raise ValueError(f"Invalid camera_id: {camera_id}")
    
    def cleanup(self):
        """Cleanup khi shutdown"""
        self.camera_1.stop()
        self.camera_2.stop()


# Singleton instance
simulated_camera_service = SimulatedCameraService()