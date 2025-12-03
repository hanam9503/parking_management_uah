#!/usr/bin/env python3
"""
Tạo file camera_offline.png để fix lỗi Stream error
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

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
    output_path = Path(__file__).parent / 'backend' / 'camera_ai' / 'static' / 'camera_offline.png'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img)
    print(f"  ✓ Offline placeholder: {output_path}")
    print(f"  ✓ File size: {os.path.getsize(output_path)} bytes")
    return output_path

if __name__ == "__main__":
    try:
        path = create_camera_offline_placeholder()
        print("\n✅ SUCCESS: camera_offline.png được tạo thành công!")
        print(f"📁 Location: {path}")
        if path.exists():
            print(f"✓ File exists: {path.is_file()}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
