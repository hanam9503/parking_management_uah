#!/usr/bin/env python
"""
Setup Camera Simulation System
Tạo folders và generate placeholder files
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')

import django
django.setup()

from pathlib import Path
from django.conf import settings
import cv2
import numpy as np

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def create_folders():
    """Tạo cấu trúc thư mục"""
    print("📁 Creating folder structure...")
    
    folders = [
        'camera_simulations/videos/checkin',
        'camera_simulations/videos/checkout',
        'camera_simulations/images',
        'camera_simulations/temp'
    ]
    
    for folder in folders:
        path = Path(settings.MEDIA_ROOT) / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {path}")

def create_placeholder_video(filename, text, duration=10):
    """Tạo video placeholder với text"""
    print(f"🎬 Creating placeholder video: {filename}")
    
    # Video properties
    width, height = 640, 480
    fps = 30
    # Thử MJPEG thay vì mp4v để tránh lỗi FFmpeg
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    
    # Output path - thay .mp4 thành .avi cho MJPEG
    output_path = Path(settings.MEDIA_ROOT) / filename
    output_path = output_path.with_suffix('.avi')
    
    # Create video writer
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    total_frames = fps * duration
    
    for frame_num in range(total_frames):
        # Create frame
        frame = np.ones((height, width, 3), dtype=np.uint8) * 50
        
        # Add gradient
        for i in range(height):
            frame[i, :] = [50 + i//5, 50 + i//5, 50 + i//5]
        
        # Add text
        cv2.putText(frame, text, (50, height//2 - 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        cv2.putText(frame, "DEMO VIDEO", (50, height//2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
        
        # Frame counter
        cv2.putText(frame, f"Frame: {frame_num}/{total_frames}", (50, height//2 + 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
        
        # Time
        time_str = f"{frame_num/fps:.1f}s / {duration}s"
        cv2.putText(frame, time_str, (50, height//2 + 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)
        
        # Add border
        cv2.rectangle(frame, (10, 10), (width-10, height-10), (100, 100, 100), 2)
        
        out.write(frame)
        
        # Progress
        if frame_num % fps == 0:
            progress = (frame_num / total_frames) * 100
            print(f"    Progress: {progress:.0f}%", end='\r')
    
    out.release()
    print(f"\n  ✓ Video created: {output_path}")

def create_placeholder_image(filename, text):
    """Tạo ảnh placeholder"""
    print(f"🖼️  Creating placeholder image: {filename}")
    
    # Image properties
    width, height = 640, 480
    
    # Create image
    img = np.ones((height, width, 3), dtype=np.uint8) * 200
    
    # Add gradient
    for i in range(height):
        img[i, :] = [200 - i//10, 200 - i//10, 200 - i//10]
    
    # Add main text
    cv2.putText(img, text, (80, height//2 - 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 50), 2)
    
    # Add subtitle
    cv2.putText(img, "Placeholder Image", (120, height//2 + 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
    
    # Draw fake license plate
    plate_x, plate_y = 200, 300
    plate_w, plate_h = 240, 80
    
    # White background
    cv2.rectangle(img, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), 
                 (255, 255, 255), -1)
    
    # Blue border
    cv2.rectangle(img, (plate_x, plate_y), (plate_x + plate_w, plate_y + plate_h), 
                 (0, 0, 255), 3)
    
    # Fake license number
    fake_plate = f"29{chr(65 + hash(filename) % 26)}{hash(filename) % 9}-{(hash(filename) % 90000) + 10000}"
    cv2.putText(img, fake_plate, (plate_x + 20, plate_y + 55),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
    
    # Add border
    cv2.rectangle(img, (10, 10), (width-10, height-10), (100, 100, 100), 2)
    
    # Save
    output_path = Path(settings.MEDIA_ROOT) / filename
    cv2.imwrite(str(output_path), img)
    print(f"  ✓ Image created: {output_path}")

def create_camera_offline_placeholder():
    """Tạo ảnh "Camera Offline" """
    print("📷 Creating camera offline placeholder...")
    
    width, height = 640, 480
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Add text
    cv2.putText(img, "CAMERA OFFLINE", (140, height//2 - 20),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 100, 100), 2)
    
    cv2.putText(img, "Please start camera from Admin Panel", (100, height//2 + 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 80, 80), 1)
    
    # Draw icon
    icon_size = 80
    icon_x, icon_y = width//2 - icon_size//2, height//2 - 150
    
    # Camera icon (simplified)
    cv2.rectangle(img, (icon_x, icon_y), (icon_x + icon_size, icon_y + 60), 
                 (100, 100, 100), 3)
    cv2.circle(img, (icon_x + icon_size//2, icon_y + 30), 20, (100, 100, 100), 3)
    cv2.line(img, (icon_x - 20, icon_y + 30), (icon_x, icon_y + 30), (100, 100, 100), 3)
    
    # Save
    output_path = Path(__file__).parent.parent / 'backend' / 'camera_ai' / 'static' / 'camera_offline.png'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img)
    print(f"  ✓ Offline placeholder: {output_path}")

def create_demo_files():
    """Tạo các file demo"""
    print("\n🎨 Creating demo files...")
    
    # Videos
    create_placeholder_video(
        'camera_simulations/videos/checkin/demo_checkin.mp4',
        'CAMERA 1 - CHECK-IN',
        duration=10
    )
    
    create_placeholder_video(
        'camera_simulations/videos/checkout/demo_checkout.mp4',
        'CAMERA 2 - CHECK-OUT',
        duration=10
    )
    
    # Images
    for i in range(1, 4):
        create_placeholder_image(
            f'camera_simulations/images/car_checkin_{i:02d}.jpg',
            f'Check-in Vehicle {i}'
        )
        
        create_placeholder_image(
            f'camera_simulations/images/car_checkout_{i:02d}.jpg',
            f'Check-out Vehicle {i}'
        )
    
    # Offline placeholder
    create_camera_offline_placeholder()

def print_usage():
    """In hướng dẫn sử dụng"""
    print_header("✅ SETUP COMPLETED!")
    
    print("""
📝 NEXT STEPS:

1️⃣ START DJANGO SERVER:
   cd backend
   python manage.py runserver

2️⃣ ADMIN - CONTROL PANEL:
   URL: http://localhost:8000/simulation/admin/control/
   Login: admin / admin123
   
   Actions:
   • Select demo video from dropdown
   • Click START to begin streaming
   • Upload your own videos/images
   • Inject images to simulate vehicles

3️⃣ SECURITY - LIVE VIEW:
   URL: http://localhost:8000/simulation/security/live/
   Login: security / security123
   
   Features:
   • Split-screen 2 cameras
   • Real-time detection overlay
   • Live log of detections
   • Fullscreen mode (F11)

📁 FILE STRUCTURE:
   media/
   └── camera_simulations/
       ├── videos/
       │   ├── checkin/
       │   │   └── demo_checkin.mp4 ✓
       │   └── checkout/
       │       └── demo_checkout.mp4 ✓
       └── images/
           ├── car_checkin_01.jpg ✓
           ├── car_checkin_02.jpg ✓
           └── ...

🎬 FOR BETTER DEMO:
   Replace placeholder videos with:
   • Real parking lot footage
   • High-quality vehicle images
   • Clear license plate shots

💡 TIPS:
   • Use MP4 format (H.264 codec)
   • Resolution: 640x480 or higher
   • Test videos work with VLC first
   • Prepare 5-10 injection images

🎉 READY FOR PRESENTATION!
    """)

def main():
    print_header("🎥 CAMERA SIMULATION SYSTEM - SETUP")
    
    try:
        # Step 1: Create folders
        create_folders()
        
        # Step 2: Create demo files
        create_demo_files()
        
        # Step 3: Print usage
        print_usage()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)