from flask import Flask, render_template, jsonify, session, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import base64
import cv2
import numpy as np
from functools import wraps

app = Flask(__name__)
app.secret_key = 'exam-system-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Make Python functions available in templates
@app.context_processor
def utility_processor():
    return dict(max=max, min=min, len=len)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    duration_minutes = db.Column(db.Integer, default=2)
    total_questions = db.Column(db.Integer, default=20)
    created_by = db.Column(db.Integer)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer)
    question_text = db.Column(db.Text)
    option_a = db.Column(db.String(255))
    option_b = db.Column(db.String(255))
    option_c = db.Column(db.String(255))
    option_d = db.Column(db.String(255))
    correct_option = db.Column(db.String(1))
    marks = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    submitted = db.Column(db.Boolean, default=False)
    cheating_count = db.Column(db.Integer, default=0)
    terminated = db.Column(db.Boolean, default=False)
    final_marks = db.Column(db.Float, default=0)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer)
    question_id = db.Column(db.Integer)
    selected_option = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean, default=False)

class CheatingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    exam_id = db.Column(db.Integer)
    attempt_id = db.Column(db.Integer)
    cheat_type = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CameraLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    exam_id = db.Column(db.Integer)
    attempt_id = db.Column(db.Integer)
    event_type = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_data = db.Column(db.Text)

# Create database and sample data
with app.app_context():
    try:
        db.drop_all()
    except:
        pass
    
    db.create_all()
    
    print("🔄 Creating fresh database...")
    
    # Create 25 students
    for i in range(1, 26):
        roll_number = f"500{i:02d}"
        username = roll_number
        password = f"{roll_number}@123"
        
        if not User.query.filter_by(username=username).first():
            student = User(
                username=username,
                password_hash=generate_password_hash(password),
                role='student',
                full_name=f"Student {roll_number}"
            )
            db.session.add(student)
            
    # Create admin
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin'),
            role='admin', 
            full_name='System Administrator'
        )
        db.session.add(admin)
    
    # Create teacher
    if not User.query.filter_by(username='teacher1').first():
        teacher = User(
            username='teacher1',
            password_hash=generate_password_hash('test123'),
            role='teacher',
            full_name='Demo Teacher'
        )
        db.session.add(teacher)
    
    # Create sample GK exam
    if not Exam.query.first():
        exam = Exam(
            title="General Knowledge Test",
            duration_minutes=2,
            total_questions=20,
            created_by=1,
            is_published=True
        )
        db.session.add(exam)
        db.session.flush()
        
        # Add sample GK questions
        gk_questions = [
            {"question": "What is the capital of France?", "options": ["London", "Berlin", "Paris", "Madrid"], "correct": "C"},
            {"question": "Which planet is known as the Red Planet?", "options": ["Venus", "Mars", "Jupiter", "Saturn"], "correct": "B"},
            {"question": "What is the largest ocean on Earth?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "correct": "D"},
            {"question": "Who wrote 'Romeo and Juliet'?", "options": ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"], "correct": "B"},
            {"question": "What is the chemical symbol for gold?", "options": ["Go", "Gd", "Au", "Ag"], "correct": "C"},
            {"question": "What is the largest mammal in the world?", "options": ["Elephant", "Blue Whale", "Giraffe", "Polar Bear"], "correct": "B"},
            {"question": "Which country is known as the Land of the Rising Sun?", "options": ["China", "Japan", "Thailand", "South Korea"], "correct": "B"},
            {"question": "What is the hardest natural substance on Earth?", "options": ["Gold", "Iron", "Diamond", "Platinum"], "correct": "C"},
            {"question": "How many continents are there?", "options": ["5", "6", "7", "8"], "correct": "C"},
            {"question": "What is the largest desert in the world?", "options": ["Sahara", "Gobi", "Arabian", "Antarctic"], "correct": "D"},
            {"question": "Which element is essential for combustion?", "options": ["Nitrogen", "Oxygen", "Hydrogen", "Carbon Dioxide"], "correct": "B"},
            {"question": "Who painted the Mona Lisa?", "options": ["Van Gogh", "Picasso", "Leonardo da Vinci", "Michelangelo"], "correct": "C"},
            {"question": "What is the smallest country in the world?", "options": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"], "correct": "B"},
            {"question": "Which gas do plants absorb from the atmosphere?", "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"], "correct": "B"},
            {"question": "What is the currency of Japan?", "options": ["Yuan", "Won", "Yen", "Ringgit"], "correct": "C"},
            {"question": "How many bones are in the human body?", "options": ["196", "206", "216", "226"], "correct": "B"},
            {"question": "Which planet is known for its rings?", "options": ["Jupiter", "Saturn", "Uranus", "Neptune"], "correct": "B"},
            {"question": "What is the main language of Brazil?", "options": ["Spanish", "Portuguese", "French", "English"], "correct": "B"},
            {"question": "Who discovered penicillin?", "options": ["Marie Curie", "Alexander Fleming", "Louis Pasteur", "Robert Koch"], "correct": "B"},
            {"question": "What is the speed of light?", "options": ["299,792 km/s", "300,000 km/s", "250,000 km/s", "350,000 km/s"], "correct": "A"}
        ]
        
        for q_data in gk_questions:
            question = Question(
                exam_id=exam.id,
                question_text=q_data["question"],
                option_a=q_data["options"][0],
                option_b=q_data["options"][1],
                option_c=q_data["options"][2],
                option_d=q_data["options"][3],
                correct_option=q_data["correct"],
                marks=1
            )
            db.session.add(question)
    
    db.session.commit()
    print("✅ Database initialized successfully!")
    print("👨‍🎓 Students: 50001@123 to 50025@123")
    print("👨‍🏫 Teacher: teacher1/test123")
    print("👨‍💼 Admin: admin/admin")

# Login required decorator
def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get(f'{role}_logged_in'):
                flash(f'Please login as {role} to access this page.', 'warning')
                return redirect(url_for(f'{role}_login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ===== ROUTES =====

@app.route('/')
def home():
    return render_template('index.html')

# ===== ADMIN ROUTES =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='admin').first()
        
        if user and check_password_hash(user.password_hash, password):
            session['admin_logged_in'] = True
            session['admin_id'] = user.id
            session['admin_name'] = user.full_name
            flash('Admin login successful!', 'success')
            return redirect('/admin/dashboard')
        flash('Invalid credentials!', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    # Get system statistics
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_exams = Exam.query.count()
    total_attempts = ExamAttempt.query.count()
    
    # Get recent activity
    recent_attempts = ExamAttempt.query.order_by(ExamAttempt.start_time.desc()).limit(10).all()
    recent_cheating = CheatingLog.query.order_by(CheatingLog.timestamp.desc()).limit(10).all()
    
    # Get all users for management
    students = User.query.filter_by(role='student').all()
    teachers = User.query.filter_by(role='teacher').all()
    
    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_exams=total_exams,
                         total_attempts=total_attempts,
                         recent_attempts=recent_attempts,
                         recent_cheating=recent_cheating,
                         students=students,
                         teachers=teachers,
                         admin_name=session.get('admin_name'))

@app.route('/admin/users')
@login_required('admin')
def admin_users():
    students = User.query.filter_by(role='student').all()
    teachers = User.query.filter_by(role='teacher').all()
    
    return render_template('admin_users.html',
                         students=students,
                         teachers=teachers,
                         admin_name=session.get('admin_name'))

@app.route('/admin/exams')
@login_required('admin')
def admin_exams():
    exams = Exam.query.all()
    return render_template('admin_exams.html',
                         exams=exams,
                         admin_name=session.get('admin_name'))

@app.route('/admin/reports')
@login_required('admin')
def admin_reports():
    # Get comprehensive reports
    exam_results = []
    exams = Exam.query.all()
    
    for exam in exams:
        attempts = ExamAttempt.query.filter_by(exam_id=exam.id, submitted=True).all()
        if attempts:
            avg_score = sum(attempt.final_marks for attempt in attempts) / len(attempts)
            pass_rate = len([a for a in attempts if a.final_marks >= exam.total_questions * 0.4]) / len(attempts) * 100
            cheating_count = len([a for a in attempts if a.cheating_count > 0])
            
            exam_results.append({
                'exam': exam,
                'total_attempts': len(attempts),
                'avg_score': avg_score,
                'pass_rate': pass_rate,
                'cheating_count': cheating_count
            })
    
    return render_template('admin_reports.html',
                         exam_results=exam_results,
                         admin_name=session.get('admin_name'))

@app.route('/admin/settings')
@login_required('admin')
def admin_settings():
    return render_template('admin_settings.html',
                         admin_name=session.get('admin_name'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out successfully!', 'info')
    return redirect('/')

# ===== STUDENT ROUTES =====

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='student').first()
        
        if user and check_password_hash(user.password_hash, password):
            session['student_logged_in'] = True
            session['student_id'] = user.id
            session['student_username'] = user.username
            session['student_name'] = user.full_name
            flash(f'Welcome {user.full_name}!', 'success')
            return redirect('/student/dashboard')
        flash('Invalid credentials!', 'danger')
    return render_template('student_login.html')

@app.route('/student/dashboard')
@login_required('student')
def student_dashboard():
    exams = Exam.query.filter_by(is_published=True).all()
    student_id = session['student_id']
    
    # Get attempt history
    attempts = ExamAttempt.query.filter_by(student_id=student_id).all()
    
    return render_template('student_dashboard.html', 
                         exams=exams, 
                         attempts=attempts,
                         student_name=session['student_name'])

@app.route('/student/start_exam/<int:exam_id>')
@login_required('student')
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    student_id = session['student_id']
    
    # Check if already attempted
    existing_attempt = ExamAttempt.query.filter_by(
        exam_id=exam_id, student_id=student_id
    ).first()
    
    if existing_attempt and existing_attempt.submitted:
        flash('You have already taken this exam!', 'warning')
        return redirect('/student/dashboard')
    
    # Create new attempt
    if not existing_attempt:
        attempt = ExamAttempt(
            exam_id=exam_id,
            student_id=student_id,
            start_time=datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.commit()
        session['current_attempt_id'] = attempt.id
    else:
        session['current_attempt_id'] = existing_attempt.id
    
    session['current_exam_id'] = exam_id
    session['exam_start_time'] = datetime.utcnow().isoformat()
    session['cheating_count'] = 0
    session['camera_warnings'] = 0
    
    return render_template('exam_page.html', exam=exam, attempt_id=session['current_attempt_id'])

@app.route('/api/exam/questions/<int:exam_id>')
@login_required('student')
def get_exam_questions(exam_id):
    questions = Question.query.filter_by(exam_id=exam_id).all()
    questions_data = []
    
    for q in questions:
        questions_data.append({
            'id': q.id,
            'text': q.question_text,
            'options': {
                'A': q.option_a,
                'B': q.option_b,
                'C': q.option_c,
                'D': q.option_d
            },
            'correct': q.correct_option,
            'marks': q.marks
        })
    
    return jsonify({'questions': questions_data})

@app.route('/api/submit_exam', methods=['POST'])
@login_required('student')
def submit_exam():
    data = request.json
    attempt_id = session.get('current_attempt_id')
    student_id = session['student_id']
    
    if not attempt_id:
        return jsonify({'error': 'No active exam'}), 400
    
    attempt = ExamAttempt.query.get(attempt_id)
    if not attempt or attempt.student_id != student_id:
        return jsonify({'error': 'Invalid attempt'}), 400
    
    # Calculate marks
    total_marks = 0
    for answer_data in data.get('answers', []):
        question = Question.query.get(answer_data['question_id'])
        is_correct = (answer_data['selected_option'] == question.correct_option)
        
        answer = Answer(
            attempt_id=attempt_id,
            question_id=answer_data['question_id'],
            selected_option=answer_data['selected_option'],
            is_correct=is_correct
        )
        db.session.add(answer)
        
        if is_correct:
            total_marks += question.marks
    
    # Apply cheating penalty
    cheating_count = session.get('cheating_count', 0)
    camera_warnings = session.get('camera_warnings', 0)
    
    # Combine both types of violations
    total_violations = cheating_count + camera_warnings
    
    if total_violations >= 3:
        total_marks = 0
        attempt.terminated = True
    elif total_violations == 2:
        total_marks = total_marks * 0.3  # 70% penalty
    elif total_violations == 1:
        total_marks = total_marks * 0.7  # 30% penalty
    
    attempt.final_marks = total_marks
    attempt.end_time = datetime.utcnow()
    attempt.submitted = True
    attempt.cheating_count = total_violations
    
    db.session.commit()
    
    # Clear session
    session.pop('current_attempt_id', None)
    session.pop('current_exam_id', None)
    session.pop('cheating_count', None)
    session.pop('camera_warnings', None)
    session.pop('camera_proctoring', None)
    
    return jsonify({
        'success': True,
        'marks': total_marks,
        'cheating_count': cheating_count,
        'camera_warnings': camera_warnings,
        'terminated': attempt.terminated
    })

@app.route('/api/record_cheating', methods=['POST'])
@login_required('student')
def record_cheating():
    data = request.json
    attempt_id = session.get('current_attempt_id')
    student_id = session['student_id']
    
    if not attempt_id:
        return jsonify({'error': 'No active exam'}), 400
    
    # Update cheating count
    cheating_count = session.get('cheating_count', 0) + 1
    session['cheating_count'] = cheating_count
    
    # Update attempt
    attempt = ExamAttempt.query.get(attempt_id)
    if attempt:
        attempt.cheating_count = max(attempt.cheating_count, cheating_count)
    
    # Log cheating event
    cheat_log = CheatingLog(
        student_id=student_id,
        exam_id=session.get('current_exam_id'),
        attempt_id=attempt_id,
        cheat_type=data.get('type', 'tab_switch')
    )
    db.session.add(cheat_log)
    db.session.commit()
    
    # Terminate if 3+ total violations (cheating + camera)
    total_violations = cheating_count + session.get('camera_warnings', 0)
    if total_violations >= 3:
        if attempt:
            attempt.terminated = True
            db.session.commit()
        return jsonify({
            'terminated': True,
            'message': 'Exam terminated due to multiple violations!'
        })
    
    return jsonify({
        'cheating_count': cheating_count,
        'warning': True if cheating_count >= 1 else False
    })

@app.route('/student/results')
@login_required('student')
def student_results():
    student_id = session['student_id']
    attempts = ExamAttempt.query.filter_by(student_id=student_id, submitted=True).all()
    
    results = []
    for attempt in attempts:
        exam = Exam.query.get(attempt.exam_id)
        # Get camera warnings for this attempt
        camera_warnings = CameraLog.query.filter_by(attempt_id=attempt.id).count()
        
        results.append({
            'exam_title': exam.title,
            'marks': attempt.final_marks,
            'total_questions': exam.total_questions,
            'cheating_count': attempt.cheating_count,
            'camera_warnings': camera_warnings,
            'terminated': attempt.terminated,
            'completion_time': attempt.end_time.strftime('%Y-%m-%d %H:%M') if attempt.end_time else 'N/A'
        })
    
    return render_template('student_results.html', results=results)

@app.route('/student/logout')
def student_logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect('/')

# ===== TEACHER ROUTES =====

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='teacher').first()
        
        if user and check_password_hash(user.password_hash, password):
            session['teacher_logged_in'] = True
            session['teacher_id'] = user.id
            session['teacher_name'] = user.full_name
            flash('Teacher login successful!', 'success')
            return redirect('/teacher/dashboard')
        flash('Invalid credentials!', 'danger')
    return render_template('teacher_login.html')

@app.route('/teacher/dashboard')
@login_required('teacher')
def teacher_dashboard():
    # Get all students with their attempt statistics
    students = User.query.filter_by(role='student').order_by(User.username).all()
    
    student_stats = []
    for student in students:
        attempts = ExamAttempt.query.filter_by(student_id=student.id).all()
        total_attempts = len(attempts)
        submitted_attempts = len([a for a in attempts if a.submitted])
        
        # Get cheating events count properly
        cheating_events = CheatingLog.query.filter_by(student_id=student.id).count()
        
        # Get camera warnings count properly
        camera_warnings = CameraLog.query.filter_by(student_id=student.id).count()
        
        student_stats.append({
            'id': student.id,
            'roll_number': student.username,
            'name': student.full_name,
            'total_attempts': total_attempts,
            'submitted_attempts': submitted_attempts,
            'cheating_events': cheating_events,
            'camera_warnings': camera_warnings,
            'terminated_exams': len([a for a in attempts if a.terminated])
        })
    
    # Get recent cheating alerts with proper joins
    recent_cheating = db.session.query(CheatingLog, User, ExamAttempt).join(
        User, CheatingLog.student_id == User.id
    ).join(
        ExamAttempt, CheatingLog.attempt_id == ExamAttempt.id
    ).order_by(CheatingLog.timestamp.desc()).limit(10).all()
    
    # Get camera logs with proper data
    recent_camera_logs = db.session.query(CameraLog, User, ExamAttempt).join(
        User, CameraLog.student_id == User.id
    ).join(
        ExamAttempt, CameraLog.attempt_id == ExamAttempt.id
    ).order_by(CameraLog.timestamp.desc()).limit(10).all()
    
    camera_stats = {
        'total_sessions': ExamAttempt.query.filter_by(submitted=False).count(),
        'total_warnings': CameraLog.query.count(),
        'clean_sessions': ExamAttempt.query.filter_by(cheating_count=0, submitted=True).count(),
        'terminated_by_camera': ExamAttempt.query.filter_by(terminated=True).count()
    }
    
    return render_template('teacher_dashboard.html',
                         student_stats=student_stats,
                         recent_cheating=recent_cheating,
                         recent_camera_logs=recent_camera_logs,
                         camera_stats=camera_stats,
                         teacher_name=session['teacher_name'])

@app.route('/teacher/student_details/<int:student_id>')
@login_required('teacher')
def student_details(student_id):
    student = User.query.get_or_404(student_id)
    attempts = ExamAttempt.query.filter_by(student_id=student_id).all()
    
    attempt_details = []
    for attempt in attempts:
        exam = Exam.query.get(attempt.exam_id)
        cheating_logs = CheatingLog.query.filter_by(attempt_id=attempt.id).all()
        camera_logs = CameraLog.query.filter_by(attempt_id=attempt.id).all()
        
        attempt_details.append({
            'exam_title': exam.title,
            'start_time': attempt.start_time,
            'end_time': attempt.end_time,
            'submitted': attempt.submitted,
            'marks': attempt.final_marks,
            'cheating_count': attempt.cheating_count,
            'terminated': attempt.terminated,
            'cheating_logs': cheating_logs,
            'camera_logs': camera_logs
        })
    
    return render_template('student_details.html',
                         student=student,
                         attempts=attempt_details)

@app.route('/teacher/exam_results')
@login_required('teacher')
def exam_results():
    exams = Exam.query.all()
    exam_results = []
    
    for exam in exams:
        attempts = ExamAttempt.query.filter_by(exam_id=exam.id, submitted=True).all()
        
        if attempts:
            results = []
            for attempt in attempts:
                student = User.query.get(attempt.student_id)
                camera_warnings = CameraLog.query.filter_by(attempt_id=attempt.id).count()
                grade = 'A' if attempt.final_marks >= 16 else 'B' if attempt.final_marks >= 12 else 'C' if attempt.final_marks >= 8 else 'F'
                
                results.append({
                    'roll_number': student.username,
                    'name': student.full_name,
                    'marks': attempt.final_marks,
                    'total_marks': exam.total_questions,
                    'grade': grade,
                    'cheating_count': attempt.cheating_count,
                    'camera_warnings': camera_warnings,
                    'terminated': attempt.terminated
                })
            
            exam_results.append({
                'exam': exam,
                'results': sorted(results, key=lambda x: x['marks'], reverse=True)
            })
    
    return render_template('exam_results.html', exam_results=exam_results)

@app.route('/teacher/create_exam', methods=['GET', 'POST'])
@login_required('teacher')
def create_exam():
    if request.method == 'POST':
        title = request.form['title']
        duration = int(request.form['duration'])
        total_questions = int(request.form['total_questions'])
        
        exam = Exam(
            title=title,
            duration_minutes=duration,
            total_questions=total_questions,
            created_by=session['teacher_id'],
            is_published=True
        )
        db.session.add(exam)
        db.session.commit()
        
        flash('Exam created successfully! Now add questions.', 'success')
        return redirect(f'/teacher/add_questions/{exam.id}')
    
    return render_template('create_exam.html')

@app.route('/teacher/add_questions/<int:exam_id>', methods=['GET', 'POST'])
@login_required('teacher')
def add_questions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']
        
        question = Question(
            exam_id=exam_id,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            marks=1
        )
        db.session.add(question)
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(f'/teacher/add_questions/{exam_id}')
    
    # Count existing questions
    existing_questions = Question.query.filter_by(exam_id=exam_id).count()
    questions_remaining = exam.total_questions - existing_questions
    
    return render_template('add_questions.html',
                         exam=exam,
                         existing_questions=existing_questions,
                         questions_remaining=questions_remaining)

@app.route('/teacher/live_updates')
@login_required('teacher')
def live_updates():
    """Provide live updates for cheating events"""
    # Get counts of recent events (last 10 seconds)
    ten_seconds_ago = datetime.utcnow() - timedelta(seconds=10)
    
    new_cheating_events = CheatingLog.query.filter(
        CheatingLog.timestamp >= ten_seconds_ago
    ).count()
    
    new_camera_events = CameraLog.query.filter(
        CameraLog.timestamp >= ten_seconds_ago
    ).count()
    
    return jsonify({
        'new_cheating_events': new_cheating_events,
        'new_camera_events': new_camera_events,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/teacher/logout')
def teacher_logout():
    session.clear()
    flash('Teacher logged out successfully!', 'info')
    return redirect('/')

# ===== CAMERA PROCTORING ROUTES =====

@app.route('/api/start_camera_proctoring', methods=['POST'])
@login_required('student')
def start_camera_proctoring():
    """Initialize camera proctoring for an exam attempt"""
    attempt_id = session.get('current_attempt_id')
    student_id = session['student_id']
    
    if not attempt_id:
        return jsonify({'error': 'No active exam'}), 400
    
    # Initialize camera monitoring session
    session['camera_proctoring'] = True
    session['camera_warnings'] = 0
    
    return jsonify({
        'status': 'started',
        'message': 'Camera proctoring initialized'
    })

@app.route('/api/process_camera_frame', methods=['POST'])
@login_required('student')
def process_camera_frame():
    """Process camera frame for AI proctoring"""
    attempt_id = session.get('current_attempt_id')
    student_id = session['student_id']
    
    if not attempt_id or not session.get('camera_proctoring'):
        return jsonify({'error': 'Camera proctoring not active'}), 400
    
    data = request.json
    image_data = data.get('image_data')
    timestamp = data.get('timestamp')
    
    # Decode base64 image
    try:
        # Remove header from base64 string
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # AI Proctoring Analysis
        analysis_result = analyze_camera_frame(image, student_id, attempt_id)
        
        # Handle violations
        if analysis_result['violation_detected']:
            handle_camera_violation(
                student_id, 
                attempt_id, 
                analysis_result['violation_type'],
                analysis_result['confidence'],
                image_data
            )
            
            return jsonify({
                'violation': True,
                'violation_type': analysis_result['violation_type'],
                'warning_count': session.get('camera_warnings', 0),
                'message': analysis_result['message']
            })
        
        return jsonify({
            'violation': False,
            'status': 'normal'
        })
        
    except Exception as e:
        print(f"Error processing camera frame: {e}")
        return jsonify({'error': 'Frame processing failed'}), 500

def analyze_camera_frame(image, student_id, attempt_id):
    """Analyze camera frame for proctoring violations"""
    try:
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Load face detection classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        result = {
            'violation_detected': False,
            'violation_type': None,
            'confidence': 0.0,
            'message': '',
            'face_count': len(faces)
        }
        
        # Check for no face detected
        if len(faces) == 0:
            result.update({
                'violation_detected': True,
                'violation_type': 'no_face_detected',
                'confidence': 0.9,
                'message': 'No face detected in frame'
            })
            return result
        
        # Check for multiple faces
        if len(faces) > 1:
            result.update({
                'violation_detected': True,
                'violation_type': 'multiple_faces_detected',
                'confidence': min(1.0, len(faces) * 0.3),
                'message': f'Multiple faces detected: {len(faces)}'
            })
            return result
        
        # Check face position and size (basic attention monitoring)
        if len(faces) == 1:
            x, y, w, h = faces[0]
            height, width = image.shape[:2]
            
            # Calculate face position metrics
            face_center_x = x + w/2
            face_center_y = y + h/2
            
            # Check if face is too small (might be looking away)
            if w < width * 0.15 or h < height * 0.15:
                result.update({
                    'violation_detected': True,
                    'violation_type': 'face_too_small',
                    'confidence': 0.7,
                    'message': 'Face appears too small - possible attention issue'
                })
                return result
            
            # Check if face is centered properly
            center_threshold = 0.3
            if (abs(face_center_x - width/2) > width * center_threshold or 
                abs(face_center_y - height/2) > height * center_threshold):
                result.update({
                    'violation_detected': True,
                    'violation_type': 'face_not_centered',
                    'confidence': 0.6,
                    'message': 'Face not properly centered in frame'
                })
                return result
        
        return result
    except Exception as e:
        print(f"Error in face detection: {e}")
        return {
            'violation_detected': False,
            'violation_type': None,
            'confidence': 0.0,
            'message': 'Face detection error',
            'face_count': 0
        }

def handle_camera_violation(student_id, attempt_id, violation_type, confidence, image_data):
    """Handle camera proctoring violations"""
    # Update warning count
    current_warnings = session.get('camera_warnings', 0) + 1
    session['camera_warnings'] = current_warnings
    
    # Log the violation
    camera_log = CameraLog(
        student_id=student_id,
        exam_id=session.get('current_exam_id'),
        attempt_id=attempt_id,
        event_type=violation_type,
        confidence=confidence,
        image_data=image_data
    )
    db.session.add(camera_log)
    
    # Update cheating count in attempt
    attempt = ExamAttempt.query.get(attempt_id)
    if attempt:
        total_violations = attempt.cheating_count + current_warnings
        attempt.cheating_count = total_violations
        db.session.commit()
    
    # If too many warnings, trigger exam termination
    total_violations = session.get('cheating_count', 0) + current_warnings
    if total_violations >= 3:
        terminate_exam_due_to_camera_violations(attempt_id)

def terminate_exam_due_to_camera_violations(attempt_id):
    """Terminate exam due to excessive camera violations"""
    attempt = ExamAttempt.query.get(attempt_id)
    if attempt and not attempt.terminated:
        attempt.terminated = True
        attempt.cheating_count = max(attempt.cheating_count, 3)
        db.session.commit()
        
        # Also log as cheating event
        cheat_log = CheatingLog(
            student_id=attempt.student_id,
            exam_id=attempt.exam_id,
            attempt_id=attempt_id,
            cheat_type='camera_violations'
        )
        db.session.add(cheat_log)
        db.session.commit()

# Force browser to not cache pages
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    print("🚀 EXAM SYSTEM STARTED!")
    print("📍 http://localhost:5000")
    print("👨‍🎓 Students: 50001@123 to 50025@123")
    print("👨‍🏫 Teacher: teacher1/test123")
    print("👨‍💼 Admin: admin/admin")
    app.run(debug=True, port=5000)