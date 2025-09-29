# Cheating_Proctoring
# Exam Proctoring System

A comprehensive online examination system with AI-powered proctoring features to ensure academic integrity during remote exams.

## 🚀 Features

### Core Functionality
- **Multi-role Authentication** (Admin, Teacher, Student)
- **Exam Management** - Create, manage, and publish exams
- **Real-time Exam Interface** with timer and question navigation
- **Results & Analytics** - Performance tracking and reporting

### Proctoring & Security
- **Tab Switching Detection** - Alerts when students switch tabs/windows
- **AI Camera Proctoring** - Real-time face detection and monitoring
- **Violation Tracking** - Comprehensive logging of suspicious activities
- **Automatic Penalties** - Score deductions based on violation severity

## 👥 User Roles

### 👨‍💼 Admin
- System overview and monitoring
- User management (students & teachers)
- Exam management and analytics
- System configuration

### 👨‍🏫 Teacher  
- Create and manage exams
- Add questions to exams
- Monitor student progress
- View detailed results and cheating alerts
- Camera proctoring logs review

### 👨‍🎓 Student
- Take available exams
- Real-time camera proctoring
- View personal results and history
- Integrity scoring

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- Webcam (for proctoring features)

### Setup Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd cheating_proctoring_new
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the system**
   - Open browser and go to: `http://localhost:5000`
   - Use the credentials below to login

## 🔑 Default Login Credentials

### Admin Access
- **Username:** `admin`
- **Password:** `admin`
- **URL:** `/admin/login`

### Teacher Access  
- **Username:** `teacher1`
- **Password:** `test123`
- **URL:** `/teacher/login`

### Student Access
- **Usernames:** `50001` to `50025`
- **Password:** `[username]@123` (e.g., `50001@123`)
- **URL:** `/student/login`

## 📁 Project Structure

```
cheating_proctoring_new/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── exam.db               # SQLite database (auto-generated)
└── templates/            # HTML templates
    ├── index.html         # Homepage
    ├── admin_dashboard.html
    ├── teacher_dashboard.html
    ├── student_dashboard.html
    ├── exam_page.html     # Exam interface
    ├── login pages...     # Various login pages
    └── results pages...   # Results and analytics
```

## 🗄 Database Models

- **User** - All system users (admin, teachers, students)
- **Exam** - Exam details and configuration
- **Question** - Exam questions and options
- **ExamAttempt** - Student exam sessions
- **Answer** - Student responses
- **CheatingLog** - Tab switching violations
- **CameraLog** - Camera proctoring events

## 🎯 Key Proctoring Features

### Tab Switching Detection
- Monitors browser tab/window focus
- Logs all switching attempts
- Progressive warnings and penalties

### Camera Proctoring
- Real-time face detection using OpenCV
- Multiple face detection
- Attention monitoring
- Evidence capture for violations

### Violation System
- **1st Violation:** 30% score penalty
- **2nd Violation:** 70% score penalty  
- **3rd Violation:** Exam termination (0 marks)

## 🚦 How to Use

### For Teachers
1. Login to teacher dashboard
2. Create new exams with "Create Exam"
3. Add questions using "Add Questions"
4. Monitor students in "Student Management"
5. Review results in "Exam Results"

### For Students
1. Login to student dashboard
2. Select available exam to start
3. Allow camera access when prompted
4. Complete exam within time limit
5. Avoid tab switching and maintain camera focus
6. View results after submission

## ⚙️ Configuration

### Exam Settings
- Default duration: 2 minutes (configurable)
- 20 questions per exam
- Multiple choice format (A, B, C, D)
- Automatic scoring

### Proctoring Settings  
- Camera check interval: 3 seconds
- Face detection confidence: 60-90%
- Maximum violations before termination: 3

## 🐛 Troubleshooting

### Common Issues

**Camera not working:**
- Ensure webcam is connected and accessible
- Allow camera permissions in browser
- Check if another app is using the camera

**Login issues:**
- Verify username/password combinations
- Check if user role matches login portal
- Clear browser cache and cookies

**Database errors:**
- Delete `exam.db` file to reset database
- Restart the application

## 📊 Monitoring & Reports

### Admin Reports
- System-wide statistics
- User activity overview
- Exam performance analytics
- Security incident reports

### Teacher Analytics  
- Individual student performance
- Cheating incident details
- Camera proctoring logs
- Class-wide progress tracking

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- SQL injection prevention
- XSS protection through template escaping
- Secure file upload handling

## 📝 License

This project is for educational purposes. Please ensure compliance with your institution's privacy and monitoring policies when deploying.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Ensure proper camera permissions
4. Check browser console for errors

---

**Note:** This system is designed for academic integrity in remote examinations. Always inform students about monitoring features and obtain necessary consent before use.
