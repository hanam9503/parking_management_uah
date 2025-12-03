# 📊 PHÂN TÍCH DỰ ÁN - Hệ Thống Quản Lý Bãi Đỗ Xe Máy Thông Minh

## I. TỔNG QUAN DỰ ÁN

### 🎯 Mục Đích
Xây dựng hệ thống quản lý bãi đỗ xe máy thông minh cho Trường Đại học Kiến trúc với:
- Nhận diện biển số xe tự động (YOLO + OCR)
- Quản lý QR code cho giảng viên
- Hệ thống check-in/check-out bảo mật
- Dashboard theo dõi thời gian thực
- Thống kê & báo cáo

### 📈 Quy Mô
- **Backend**: Django 4.2.7 + PyMongo (MongoDB Atlas)
- **Database**: MongoDB (NoSQL) cho app + SQLite cho Django admin
- **AI/ML**: YOLO v8 + EasyOCR (nhận diện biển số)
- **Frontend**: HTML/CSS/JavaScript + Chart.js
- **Infrastructure**: Camera simulation system (phục vụ testing)

---

## II. KIẾN TRÚC HỆ THỐNG

```
parking_management_uah/
├── backend/                     # Django application
│   ├── parking_project/         # Main config & URLconf
│   │   ├── settings.py         # Django settings
│   │   ├── urls.py             # URL routing
│   │   └── wsgi.py
│   ├── users/                  # Authentication & Authorization
│   │   ├── models.py           # User, Teacher models
│   │   ├── views.py            # Auth & dashboard views
│   │   ├── decorators.py       # @login_required, @admin_required, etc.
│   │   └── urls.py
│   ├── vehicles/               # Vehicle management
│   │   ├── models.py           # Vehicle, QRCode models
│   │   ├── views.py            # CRUD + QR generation
│   │   └── urls.py
│   ├── parking/                # Parking management
│   │   ├── models.py           # ParkingHistory, ParkingConfig
│   │   ├── views.py
│   │   └── urls.py
│   ├── university/             # Faculty statistics
│   │   ├── models.py           # UniversityConfig, FacultyStats
│   │   ├── views.py            # Stats endpoints
│   │   └── urls.py
│   ├── camera_ai/              # AI-powered camera system ⭐ CORE
│   │   ├── service.py          # CameraAIService (YOLO + OCR)
│   │   ├── views.py            # QR scan + detection API
│   │   ├── simulation.py        # SimulatedCamera (testing)
│   │   ├── simulation_views.py  # Admin control panel
│   │   ├── urls.py
│   │   ├── models/             # YOLO weights
│   │   └── static/             # JS controls
│   ├── core/                   # Database & utilities
│   │   ├── mongodb.py          # MongoDB connection (Singleton)
│   │   └── utils.py            # Helper functions
│   ├── templates/              # HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── admin/              # Admin dashboards
│   │   ├── security/           # Security dashboards
│   │   ├── teacher/            # Teacher dashboards
│   │   ├── camera_ai/          # Camera control UI
│   │   └── components/         # Reusable components
│   ├── static/                 # CSS, JS, images
│   ├── media/                  # User uploads
│   │   ├── qr_codes/           # Generated QR codes
│   │   ├── vehicle_images/     # Vehicle photos
│   │   └── camera_simulations/ # Demo videos/images
│   ├── manage.py
│   ├── db.sqlite3              # Django sessions & admin
│   └── requirements.txt
├── scripts/
│   ├── init_mongodb.py         # Initialize MongoDB
│   ├── init_parking_config.py  # Setup parking slots
│   ├── init_university.py      # Setup faculty data
│   ├── seed_data.py            # Test data
│   ├── test_connection.py      # Verify connections
│   └── setup_camera_simulation.py # Setup camera demo files
└── .gitignore, README.md
```

---

## III. CÁC MODULE CHÍNH

### 3.1. **USERS MODULE** (Xác thực & Phân quyền)

#### Models
- **User**: Người dùng hệ thống
  - Fields: `username`, `password_hash`, `email`, `full_name`, `phone`, `role`
  - Roles: `admin`, `teacher`, `security`
  - Methods: `create()`, `authenticate()`, `get_by_id()`, `update()`, `delete()`
  
- **Teacher**: Thông tin giảng viên
  - Fields: `user_id`, `employee_id`, `faculty`, `department`, `specialized_area`
  - Methods: `create()`, `get_by_user_id()`, `get_with_user_info()`

#### Views
- `login_view()` - Đăng nhập
- `logout_view()` - Đăng xuất
- `admin_dashboard()` - Dashboard quản trị
- `admin_teachers_list()` - Quản lý giảng viên
- `security_dashboard()` - Dashboard an ninh
- `teacher_dashboard()` - Dashboard giảng viên

#### Decorators
```python
@login_required          # Yêu cầu đăng nhập
@admin_required          # Yêu cầu role = admin
@security_required       # Yêu cầu role = security
@teacher_required        # Yêu cầu role = teacher
```

---

### 3.2. **VEHICLES MODULE** (Quản lý xe & QR)

#### Models
- **Vehicle**: Thông tin xe
  - Fields: `teacher_id`, `license_plate`, `vehicle_type`, `brand`, `color`
  - Types: `motorcycle`, `car`, `bicycle`
  - Methods: `create()`, `get_by_license_plate()`, `get_by_teacher()`
  - Features: Normalization (uppercase, remove spaces)
  
- **QRCode**: QR code cho xe
  - Format: `VEHICLE_ID|LICENSE_PLATE`
  - Methods: `generate()`, `get_by_vehicle()`, `verify()`
  - Stored: PNG files + MongoDB metadata

#### Views
- Admin: `admin_vehicles_list()`, `admin_vehicles_form()`, `admin_vehicles_delete()`
- Teacher: `teacher_vehicles_list()`, `teacher_vehicles_form()`, `teacher_view_qr()`

#### Features
- ✅ Automatic QR generation
- ✅ License plate normalization
- ✅ Duplicate prevention
- ✅ Teacher-vehicle relationship

---

### 3.3. **PARKING MODULE** (Lịch sử & Cấu hình bãi)

#### Models
- **ParkingConfig**: Cấu hình bãi
  - Vehicle types: motorcycle (150), car (50), bicycle (100)
  - Fields: `vehicle_type`, `total_capacity`, `current_occupied`
  - Methods: `init_default()`, `update_occupied()`, `get_all()`
  
- **ParkingHistory**: Lịch sử ra vào
  - Fields: `vehicle_id`, `time_in`, `time_out`, `detected_plate`, `status`
  - Status: `inside`, `completed`
  - Methods: `checkin()`, `checkout()`, `get_current_parking()`, `get_today()`
  - Features: Auto-update `ParkingConfig` on check-in/out

#### Key Logic
```python
# CHECK-IN FLOW
1. Verify QR: Vehicle exists + License plate matches DB
2. Run camera detection (YOLO TOP 3)
3. Compare TOP 3 detected plates vs QR
4. Create parking history record
5. Update ParkingConfig: current_occupied += 1
6. Return: Best detection or QR fallback

# CHECK-OUT FLOW
1. Find active record: status='inside'
2. Update: time_out, status='completed'
3. Update ParkingConfig: current_occupied -= 1
```

---

### 3.4. **CAMERA_AI MODULE** ⭐ (CORE - Nhận Diện Biển Số)

#### CameraAIService (service.py)
**Core AI engine sử dụng:**
- **YOLO v8**: Nhận diện biển số (custom model: `license-plate-finetune-v1m.pt`)
- **EasyOCR**: Trích xuất text từ biển số (hỗ trợ tiếng Anh + Việt)

**Key Methods:**
```python
process_vehicle_entry(qr_plate, entry_type)
  └─ TOP 3 Detection System:
     1. Capture frame từ camera
     2. YOLO detect tất cả biển số (confidence > 0.5)
     3. Sort by confidence, lấy TOP 3
     4. OCR từng biển số
     5. So sánh TOP 3 vs QR normalized
     6. Return: best match + all_detections[] + camera_failed flag
     └─ Fallback: Nếu camera fail → dùng QR data
```

**Confidence System:**
```python
- Detected text vs QR: similarity matching
- All detections returned with confidence scores
- Fallback to QR if no good match
```

**Detection Improvements:**
- ✅ TOP 3 ranking (instead of single best)
- ✅ Vehicle ID parsing from QR
- ✅ All detections for debugging
- ✅ Camera failure graceful degradation

#### QR Verification (views.py - process_qr_scan)
**Strict Validation Chain:**
```python
1. Parse QR: VEHICLE_ID|LICENSE_PLATE
2. Check 1: Vehicle exists? → Vehicle.get_by_id(vehicle_id)
3. Check 2: License plate matches DB? → vehicle.license_plate == qr_plate
4. ONLY IF PASSED: Call camera service
5. Check-in with detection result or QR fallback
6. Return: Error codes if validation fails
   - VEHICLE_NOT_FOUND
   - INVALID_QR
```

#### SimulatedCamera (simulation.py)
**For testing without real camera:**
- 2 simulated cameras: `camera_1` (check-in), `camera_2` (check-out)
- Can run videos or inject single images
- Returns MJPEG stream or JPEG frames
- Frame generator with timestamp

#### SimulationViews (simulation_views.py)
**Admin Control Panel:**
- Upload demo videos (check-in, check-out)
- Upload test images
- Start/stop cameras
- Inject images into stream
- Real-time status updates

**Security Live View:**
- Split-screen: 2 cameras
- Live detection overlay
- Detection log

**API Endpoints:**
```
POST /simulation/api/camera/start/      # Start camera
POST /simulation/api/camera/stop/       # Stop camera
POST /simulation/api/inject/            # Inject image
GET  /simulation/api/status/            # Get status
GET  /simulation/frame/{camera_id}/     # Get JPEG frame (for preview)
GET  /simulation/stream/{camera_id}/    # MJPEG stream (old)
```

---

### 3.5. **UNIVERSITY MODULE** (Thống kê)

#### Models
- **UniversityConfig**: Thông tin trường
- **FacultyStats**: Thống kê theo khoa

#### Views
- `faculty_stats_list()` - List all faculties
- `system_stats()` - Overall statistics

---

### 3.6. **CORE MODULE** (Database & Utils)

#### MongoDB (core/mongodb.py)
```python
# Singleton Pattern
mongodb = MongoDB()
db = mongodb.get_db()

# Collections
users_collection
teachers_collection
vehicles_collection
qr_codes_collection
parking_history_collection
parking_config_collection
faculty_stats_collection
```

**Connection Strategy:**
- MongoDB Atlas for main app data (MongoDB)
- SQLite for Django sessions + admin (Django ORM)

#### Utils (core/utils.py)
- `hash_password()` - Bcrypt hashing
- `verify_password()` - Bcrypt verification
- `str_to_objectid()` - String → ObjectId conversion
- `get_current_timestamp()` - Server-side timestamps

---

## IV. FLOW ĐẠI DIỆN

### 🔐 Authentication Flow
```
Login Page
  └─ POST login_view()
     └─ User.authenticate(username, password)
        └─ Verify password hash (bcrypt)
        └─ Set session variables
        └─ Redirect to dashboard (by role)
```

### 🚗 Vehicle Check-In Flow
```
Security Officer → Scanner QR Code
  └─ POST /camera/api/scan/
     └─ process_qr_scan(qr_data)
        ├─ Parse: VEHICLE_ID|LICENSE_PLATE
        ├─ Verify 1: Vehicle exists?
        ├─ Verify 2: License plate matches DB?
        ├─ Call: camera_service.process_vehicle_entry()
        │  ├─ Capture frame (simulated camera)
        │  ├─ YOLO detect TOP 3 plates
        │  ├─ EasyOCR text extraction
        │  ├─ Compare TOP 3 vs QR
        │  └─ Return: best match + all detections
        ├─ ParkingHistory.checkin()
        │  ├─ Create history record
        │  ├─ Update parking_config.current_occupied += 1
        │  └─ Return: checkin_id
        └─ Response: Success + vehicle info
```

### 📊 Admin Dashboard Flow
```
Admin Login
  └─ admin_dashboard()
     ├─ Camera status card
     │  └─ 2 cameras: online/offline
     │  └─ Current video filename
     ├─ Quick stats
     │  ├─ Total today
     │  ├─ Current inside
     │  └─ Capacity by type
     └─ Recent history
```

---

## V. DATABASE SCHEMA

### Collections (MongoDB)

#### users
```json
{
  "_id": ObjectId,
  "username": "admin",
  "password_hash": "bcrypt_hash",
  "email": "admin@uah.edu.vn",
  "full_name": "Quản Trị Viên",
  "phone": "0123456789",
  "role": "admin|teacher|security",
  "is_active": true,
  "created_at": ISODate,
  "last_login": ISODate
}
```

#### teachers
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "employee_id": "GV001",
  "faculty": "Kiến Trúc",
  "department": "Thiết Kế",
  "specialized_area": "UX Design",
  "created_at": ISODate
}
```

#### vehicles
```json
{
  "_id": ObjectId,
  "teacher_id": ObjectId,
  "license_plate": "29A12345",
  "vehicle_type": "motorcycle|car|bicycle",
  "brand": "Honda",
  "color": "Đen",
  "is_active": true,
  "created_at": ISODate
}
```

#### qr_codes
```json
{
  "_id": ObjectId,
  "vehicle_id": ObjectId,
  "qr_data": "ObjectId|29A12345",
  "qr_image_path": "qr_codes/qr_xxx.png",
  "secret_key": ObjectId,
  "is_active": true,
  "created_at": ISODate
}
```

#### parking_history
```json
{
  "_id": ObjectId,
  "vehicle_id": ObjectId,
  "security_id": ObjectId,
  "time_in": ISODate,
  "time_out": ISODate,
  "detected_plate": "29A12345",
  "qr_license_plate": "29A12345",
  "status": "inside|completed",
  "notes": "Camera detected successfully"
}
```

#### parking_config
```json
{
  "_id": ObjectId,
  "vehicle_type": "motorcycle|car|bicycle",
  "total_capacity": 150,
  "current_occupied": 45,
  "created_at": ISODate
}
```

---

## VI. TECHNOLOGY STACK PHÂN TÍCH

### Backend
| Component | Version | Purpose |
|-----------|---------|---------|
| Django | 4.2.7 | Web framework |
| PyMongo | 4.6.0 | MongoDB driver |
| YOLO | v8 (ultralytics) | License plate detection |
| EasyOCR | Latest | Text recognition |
| bcrypt | 4.1.1 | Password hashing |
| QRCode | 7.4.2 | QR generation |
| Pillow | 10.1.0 | Image processing |

### Database
| Type | Purpose | Collections |
|------|---------|-------------|
| MongoDB Atlas | Main app data | users, teachers, vehicles, qr_codes, parking_history, parking_config |
| SQLite | Django sessions, admin | django_session, django_user, etc. |

### Frontend
| Technology | Purpose |
|-----------|---------|
| HTML5 | Templates |
| Bootstrap/CSS3 | Styling |
| Chart.js | Real-time charts |
| JavaScript | Interactivity |
| Fetch API | AJAX requests |

---

## VII. NHỮNG GÌ CẦN THIẾT + KHÔNG CẦN THIẾT

### ✅ CẦN THIẾT (Phục vụ chức năng core)

1. **camera_ai/** - AI detection engine (YOLO + OCR)
   - service.py: Detection logic
   - simulation.py: Test camera system
   - views.py: QR verification + API
   - simulation_views.py: Admin control panel

2. **users/** - Authentication & authorization
   - models.py, views.py, decorators.py, urls.py

3. **vehicles/** - Vehicle management + QR codes
   - models.py, views.py, urls.py

4. **parking/** - Parking history & config
   - models.py, views.py

5. **university/** - Faculty data & statistics
   - models.py, views.py (basic)

6. **core/** - Database & utilities
   - mongodb.py (Singleton), utils.py

7. **templates/** - Web UI
   - login.html, admin/, teacher/, security/, camera_ai/

8. **static/** - CSS, JS, images

9. **requirements.txt** - Dependencies

---

### ⚠️ CÓ THỂ LƯỢC BỎ (Low priority)

1. **parking app** (Django native models)
   - ✅ Keep: models.py (ParkingHistory, ParkingConfig)
   - ✅ Keep: views.py (core logic)
   - ❌ Delete: tests.py, admin.py (not used - using MongoDB)

2. **vehicles/migrations/**
   - ❌ Delete: All migrations (not using Django ORM)

3. **core/utils.py** - Utility functions
   - Some functions used everywhere
   - ✅ Keep: hash_password, verify_password, str_to_objectid, timestamps

4. **test_*.py files** in backend/
   - test_dashboard.py
   - test_session.py
   - test_teacher.py
   - ❌ Can delete (for production)
   - ✅ Keep: For development/debugging

5. **camera_ai/captured_images/**
   - ❌ Delete: Auto-cleanup or not essential

6. **Django Admin (/admin/)**
   - ✅ Keep: For emergency access
   - Can disable if not needed

7. **Django Migrations**
   - ❌ Delete: All Django migrations (only SQLite sessions needed)
   - Keep: apps structure

---

## VIII. OPTIMIZATIONS & IMPROVEMENTS

### 🚀 Performance

**Current Bottlenecks:**
1. YOLO inference: ~500ms per frame
2. EasyOCR: ~100ms per plate
3. MongoDB Atlas: Network latency

**Solutions:**
- Cache YOLO model in memory (done)
- Batch process: multiple plates at once
- Connection pooling for MongoDB
- Async task queue (Celery) for heavy tasks
- Redis for session caching

### 🔒 Security

**Current Implementation:**
- ✅ Password hashing (bcrypt)
- ✅ Session-based authentication
- ✅ Role-based decorators
- ✅ CSRF protection

**Can Improve:**
- Two-factor authentication (2FA)
- API rate limiting
- HTTPS enforcement
- Input validation & sanitization
- SQL injection protection (already using MongoDB)

### 📊 Monitoring

**Current:**
- Basic logging to console
- No persistent logging

**Add:**
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Sentry for error tracking
- APM (Application Performance Monitoring)

---

## IX. DEPENDENCIES (requirements.txt)

### Essential ✅
```
Django==4.2.7               # Framework
pymongo==4.6.0              # MongoDB driver
dnspython==2.4.2            # MongoDB Atlas DNS
PyJWT==2.8.0                # JWT (future)
bcrypt==4.1.1               # Password hashing
qrcode==7.4.2               # QR generation
Pillow==10.1.0              # Image processing
ultralytics==8.x.x          # YOLO
easyocr==1.x.x              # OCR
python-dotenv==1.0.0        # .env loading
python-dateutil==2.8.2      # Date utilities
```

### Optional (Can remove if not used)
```
django-cors-headers         # CORS headers (not used)
channels                    # WebSockets (not used)
celery                      # Task queue (not used yet)
```

---

## X. FILE STRUCTURE - CLEANUP PLAN

### 🗑️ Can Delete
```
backend/
├── parking/migrations/          # All (using MongoDB)
├── vehicles/migrations/         # All (using MongoDB)
├── parking/admin.py            # Django admin (not using)
├── parking/tests.py            # Move to separate test folder
├── vehicles/tests.py
├── test_dashboard.py           # Move to /tests/
├── test_session.py
├── test_teacher.py
├── camera_ai/captured_images/  # Auto-cleanup
```

### ✅ Keep
```
backend/
├── users/
├── vehicles/
├── parking/
├── university/
├── camera_ai/                  # CORE ⭐
├── core/
├── templates/
├── static/
├── media/
├── manage.py
└── requirements.txt
```

---

## XI. DEPLOYMENT NOTES

### Production Checklist
- [ ] Set `DEBUG=False` in settings.py
- [ ] Set random `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with domain
- [ ] Setup MongoDB Atlas with IP whitelist
- [ ] Add SSL/HTTPS
- [ ] Configure CORS if frontend separate
- [ ] Setup logging (Sentry/ELK)
- [ ] Database backups
- [ ] Email notifications
- [ ] Rate limiting on APIs

### Environment Variables (.env)
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=parkingDBsql
```

---

## XII. TỔNG KẾT

### 📊 Project Metrics
| Metric | Value |
|--------|-------|
| Django Apps | 6 (users, vehicles, parking, university, camera_ai, core) |
| MongoDB Collections | 7 |
| API Endpoints | 20+ |
| Template Files | 15+ |
| Lines of Code (Backend) | ~3000 |
| AI Models | YOLO v8 + EasyOCR |

### 🎯 Key Features
✅ QR-based vehicle management
✅ Real-time license plate recognition (YOLO + OCR)
✅ Automatic check-in/check-out
✅ Role-based access control (admin, teacher, security)
✅ Dashboard with real-time statistics
✅ Camera simulation for testing
✅ Faculty-based statistics

### ⚡ Performance Profile
- YOLO inference: ~500ms
- EasyOCR: ~100ms
- DB query: <100ms (MongoDB)
- Total check-in time: ~2-3 seconds

### 💡 Next Steps
1. Add 2FA for security
2. Implement Celery for async tasks
3. Add comprehensive logging (ELK)
4. Performance optimization (YOLO quantization)
5. Mobile app for teachers (Flutter/React Native)

---

**Generated**: December 2, 2025
**Project Language**: Vietnamese + English
**Framework**: Django 4.2.7 + MongoDB Atlas + YOLO v8
