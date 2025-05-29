import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import face_recognition
import mysql.connector
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np
import os
from tkinter.font import Font
import threading

class EnhancedFaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Face Recognition Attendance System")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        # Configure styles
        self.configure_styles()
        
        # Database connection
        self.conn = None
        self.cursor = None
        self.connect_to_db()
        self.create_tables()  # Ensure tables exist
        
        # Video capture
        self.video_capture = None
        self.current_frame = None
        self.running = False
        self.attendance_running = False
        
        # Face recognition variables
        self.known_encodings = []
        self.known_students = []
        self.load_registered_students()
        
        # Threshold for face recognition
        self.face_recognition_threshold = 0.6
        
        # GUI Elements
        self.create_widgets()
        
    def configure_styles(self):
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10), padding=5)
        self.style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        self.style.configure('Success.TLabel', foreground='green')
        self.style.configure('Error.TLabel', foreground='red')
        
    def connect_to_db(self):
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="lashchou",
                database="attendance_db",
                autocommit=True
            )
            self.cursor = self.conn.cursor(dictionary=True)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
    
    def create_tables(self):
        try:
            # Students table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    age INT,
                    gender VARCHAR(20),
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    image_path VARCHAR(255),
                    face_encoding BLOB,
                    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_name (name)
                )
            """)
            
            # Attendance table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT,
                    date DATE NOT NULL,
                    time_in DATETIME,
                    time_out DATETIME,
                    status VARCHAR(20),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    UNIQUE KEY unique_attendance (student_id, date)
                )
            """)
            
            # Courses table (optional for future expansion)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    course_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT
                )
            """)
            
            # Student courses (junction table)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_courses (
                    student_id INT,
                    course_id INT,
                    PRIMARY KEY (student_id, course_id),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (course_id) REFERENCES courses(course_id)
                )
            """)
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to create tables: {str(e)}")
    
    def load_registered_students(self):
        try:
            self.cursor.execute("SELECT * FROM students")
            students = self.cursor.fetchall()
            
            self.known_encodings = []
            self.known_students = []
            
            for student in students:
                if student['face_encoding']:
                    encoding = np.frombuffer(student['face_encoding'], dtype=np.float64)
                    self.known_encodings.append(encoding)
                    self.known_students.append(student)
                    
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load students: {str(e)}")
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Frame - Controls
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Right Frame - Video and Attendance
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Student Registration Section
        reg_frame = ttk.LabelFrame(left_frame, text="Student Registration", padding=10)
        reg_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(reg_frame, text="Student Image:").pack(anchor=tk.W)
        self.image_path = tk.StringVar()
        img_entry = ttk.Entry(reg_frame, textvariable=self.image_path, width=30)
        img_entry.pack(anchor=tk.W, fill=tk.X, pady=2)
        ttk.Button(reg_frame, text="Browse", command=self.browse_image).pack(anchor=tk.W, pady=5)
        
        # Preview image
        self.image_preview = ttk.Label(reg_frame)
        self.image_preview.pack(pady=5)
        
        # Student Details
        ttk.Label(reg_frame, text="Full Name:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(reg_frame)
        self.name_entry.pack(anchor=tk.W, fill=tk.X, pady=2)
        
        ttk.Label(reg_frame, text="Age:").pack(anchor=tk.W)
        self.age_entry = ttk.Entry(reg_frame)
        self.age_entry.pack(anchor=tk.W, fill=tk.X, pady=2)
        
        ttk.Label(reg_frame, text="Gender:").pack(anchor=tk.W)
        self.gender_combobox = ttk.Combobox(reg_frame, values=["Male", "Female", "Other"])
        self.gender_combobox.pack(anchor=tk.W, fill=tk.X, pady=2)
        
        ttk.Label(reg_frame, text="Email:").pack(anchor=tk.W)
        self.email_entry = ttk.Entry(reg_frame)
        self.email_entry.pack(anchor=tk.W, fill=tk.X, pady=2)
        
        ttk.Label(reg_frame, text="Phone:").pack(anchor=tk.W)
        self.phone_entry = ttk.Entry(reg_frame)
        self.phone_entry.pack(anchor=tk.W, fill=tk.X, pady=2)
        
        ttk.Button(reg_frame, text="Register Student", command=self.register_student, 
                  style='Accent.TButton').pack(fill=tk.X, pady=10)
        
        # Attendance Control Section
        att_frame = ttk.LabelFrame(left_frame, text="Attendance Control", padding=10)
        att_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(att_frame, text="Start Camera", command=self.start_camera).pack(fill=tk.X, pady=5)
        ttk.Button(att_frame, text="Start Attendance", command=self.start_attendance).pack(fill=tk.X, pady=5)
        ttk.Button(att_frame, text="Stop Attendance", command=self.stop_attendance).pack(fill=tk.X, pady=5)
        ttk.Button(att_frame, text="Stop Camera", command=self.stop_camera).pack(fill=tk.X, pady=5)
        
        # Settings Section
        settings_frame = ttk.LabelFrame(left_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text="Recognition Threshold:").pack(anchor=tk.W)
        self.threshold_slider = ttk.Scale(settings_frame, from_=0.3, to=1.0, value=self.face_recognition_threshold,
                                        command=lambda v: setattr(self, 'face_recognition_threshold', float(v)))
        self.threshold_slider.pack(fill=tk.X, pady=5)
        
        # Video Display
        video_frame = ttk.LabelFrame(right_frame, text="Camera Feed", padding=10)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.video_label = ttk.Label(video_frame, text="Camera feed will appear here", anchor=tk.CENTER)
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Attendance Log
        log_frame = ttk.LabelFrame(right_frame, text="Attendance Log", padding=10)
        log_frame.pack(fill=tk.BOTH, pady=5)
        
        self.attendance_tree = ttk.Treeview(log_frame, columns=("name", "time", "status"), show="headings")
        self.attendance_tree.heading("name", text="Name")
        self.attendance_tree.heading("time", text="Time")
        self.attendance_tree.heading("status", text="Status")
        self.attendance_tree.column("name", width=150)
        self.attendance_tree.column("time", width=120)
        self.attendance_tree.column("status", width=80)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)
        
        self.attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Student Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        if file_path:
            self.image_path.set(file_path)
            self.show_image_preview(file_path)
    
    def show_image_preview(self, image_path):
        try:
            image = Image.open(image_path)
            image.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(image)
            
            self.image_preview.config(image=photo)
            self.image_preview.image = photo  # Keep a reference
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {str(e)}")
    
    def register_student(self):
        image_path = self.image_path.get()
        name = self.name_entry.get().strip()
        age = self.age_entry.get().strip()
        gender = self.gender_combobox.get().strip()
        email = self.email_entry.get().strip()
        phone = self.phone_entry.get().strip()
        
        if not all([image_path, name]):
            messagebox.showwarning("Input Error", "Name and image are required fields")
            return
            
        try:
            # Load and encode the face
            known_image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(known_image)
            
            if not face_encodings:
                messagebox.showerror("Face Detection", "No face found in the image")
                return
                
            face_encoding = face_encodings[0]
            encoding_bytes = face_encoding.tobytes()
            
            # Save image to a dedicated folder
            os.makedirs("student_images", exist_ok=True)
            new_image_path = os.path.join("student_images", f"{name.replace(' ', '_')}.jpg")
            os.replace(image_path, new_image_path)
            
            # Insert into database
            self.cursor.execute(
                """INSERT INTO students 
                (name, age, gender, email, phone, image_path, face_encoding) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (name, age, gender, email, phone, new_image_path, encoding_bytes)
            )
            
            # Update in-memory data
            self.known_encodings.append(face_encoding)
            self.known_students.append({
                'student_id': self.cursor.lastrowid,
                'name': name,
                'age': age,
                'gender': gender,
                'email': email,
                'phone': phone,
                'image_path': new_image_path
            })
            
            messagebox.showinfo("Success", "Student registered successfully!")
            self.clear_registration_form()
            
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "A student with this name already exists")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register student: {str(e)}")
    
    def clear_registration_form(self):
        self.image_path.set("")
        self.name_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.gender_combobox.set("")
        self.email_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.image_preview.config(image=None)
        self.image_preview.image = None
    
    def start_camera(self):
        if self.running:
            return
            
        try:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                raise Exception("Could not open video device")
                
            self.running = True
            self.status_var.set("Camera: ON")
            self.update_video()
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to start camera: {str(e)}")
            self.stop_camera()
    
    def stop_camera(self):
        self.running = False
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        if hasattr(self.video_label, 'imgtk'):
            self.video_label.config(image=None)
        self.video_label.config(text="Camera feed stopped")
        self.status_var.set("Camera: OFF")
    
    def start_attendance(self):
        if not self.running:
            messagebox.showwarning("Camera Error", "Please start the camera first")
            return
            
        if not self.known_students:
            messagebox.showwarning("Setup Error", "No students registered for attendance")
            return
            
        if self.attendance_running:
            return
            
        self.attendance_running = True
        self.status_var.set("Attendance: ON - Recognizing faces...")
    
    def stop_attendance(self):
        self.attendance_running = False
        self.status_var.set("Attendance: OFF")
    
    def update_video(self):
        if not self.running:
            return
            
        ret, frame = self.video_capture.read()
        if ret:
            # Convert to RGB and resize for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (640, 480))
            
            # Face detection and recognition
            if self.attendance_running and self.known_encodings:
                self.process_faces(frame_rgb)
            
            # Convert to PhotoImage
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update the label
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
        self.root.after(10, self.update_video)
    
    def process_faces(self, frame):
        # Find all face locations and encodings in the current frame
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_encodings, 
                face_encoding,
                tolerance=self.face_recognition_threshold
            )
            
            face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                student = self.known_students[best_match_index]
                confidence = 1 - face_distances[best_match_index]
                
                # Mark attendance if confidence is high enough
                if confidence > self.face_recognition_threshold:
                    self.mark_attendance(student)
                    
                    # Draw rectangle and info
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, student['name'], (left, top - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(frame, f"Confidence: {confidence:.2f}", (left, bottom + 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            else:
                # Unknown face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown", (left, top - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    def mark_attendance(self, student):
        today = datetime.now().date()
        
        try:
            # Check if attendance already marked today
            self.cursor.execute(
                "SELECT * FROM attendance WHERE student_id = %s AND date = %s",
                (student['student_id'], today)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                # Update time_out if exists
                if not existing['time_out']:
                    self.cursor.execute(
                        "UPDATE attendance SET time_out = %s WHERE attendance_id = %s",
                        (datetime.now(), existing['attendance_id'])
                    )
                    self.add_to_log(student['name'], "Checked Out")
            else:
                # Insert new attendance record
                self.cursor.execute(
                    """INSERT INTO attendance 
                    (student_id, date, time_in, status) 
                    VALUES (%s, %s, %s, %s)""",
                    (student['student_id'], today, datetime.now(), "Present")
                )
                self.add_to_log(student['name'], "Checked In")
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to mark attendance: {str(e)}")
    
    def add_to_log(self, name, status):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.attendance_tree.insert("", tk.END, values=(name, current_time, status))
        
        # Auto-scroll to the bottom
        self.attendance_tree.yview_moveto(1)
    
    def on_closing(self):
        self.stop_attendance()
        self.stop_camera()
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedFaceRecognitionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()