import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import face_recognition
import mysql.connector
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance System")
        
        # Database connection
        self.conn = None
        self.cursor = None
        self.connect_to_db()
        
        # GUI Elements
        self.create_widgets()
        
        # Video capture
        self.video_capture = None
        self.current_frame = None
        self.running = False
        
        # Face recognition variables
        self.known_encoding = None
        self.known_name = ""
        self.known_age = ""
        self.known_gender = ""
        self.student_registered = False
        
    def connect_to_db(self):
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="lashchou",
                database="attendance_db"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
    
    def create_widgets(self):
        # Left Frame - Controls
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Image Selection
        tk.Label(left_frame, text="Student Image:").pack(anchor=tk.W)
        self.image_path = tk.StringVar()
        tk.Entry(left_frame, textvariable=self.image_path, width=30).pack(anchor=tk.W)
        tk.Button(left_frame, text="Browse", command=self.browse_image).pack(anchor=tk.W, pady=5)
        
        # Student Details
        tk.Label(left_frame, text="Student Name:").pack(anchor=tk.W)
        self.name_entry = tk.Entry(left_frame)
        self.name_entry.pack(anchor=tk.W, fill=tk.X, pady=5)
        
        tk.Label(left_frame, text="Student Age:").pack(anchor=tk.W)
        self.age_entry = tk.Entry(left_frame)
        self.age_entry.pack(anchor=tk.W, fill=tk.X, pady=5)
        
        tk.Label(left_frame, text="Student Gender:").pack(anchor=tk.W)
        self.gender_entry = tk.Entry(left_frame)
        self.gender_entry.pack(anchor=tk.W, fill=tk.X, pady=5)
        
        # Buttons
        tk.Button(left_frame, text="Register Student", command=self.register_student).pack(fill=tk.X, pady=10)
        tk.Button(left_frame, text="Start Attendance", command=self.start_attendance).pack(fill=tk.X, pady=5)
        tk.Button(left_frame, text="Stop Attendance", command=self.stop_attendance).pack(fill=tk.X, pady=5)
        
        # Right Frame - Video Display
        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        self.video_label = tk.Label(right_frame, text="Video feed will appear here")
        self.video_label.pack(expand=True, fill=tk.BOTH)
        
    def browse_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_path.set(file_path)
            
    def register_student(self):
        image_path = self.image_path.get()
        name = self.name_entry.get()
        age = self.age_entry.get()
        gender = self.gender_entry.get()
        
        if not all([image_path, name, age, gender]):
            messagebox.showwarning("Input Error", "Please fill all fields")
            return
            
        try:
            # Load and encode the face
            known_image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(known_image)
            
            if not face_encodings:
                messagebox.showerror("Face Detection", "No face found in the image")
                return
                
            self.known_encoding = face_encodings[0]
            self.known_name = name
            self.known_age = age
            self.known_gender = gender
            self.student_registered = True
            
            # Insert into database
            self.cursor.execute(
                "INSERT INTO students (name, age, gender, attendance_status) VALUES (%s, %s, %s, %s)",
                (name, age, gender, "Absent")
            )
            self.conn.commit()
            
            messagebox.showinfo("Success", "Student registered successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register student: {str(e)}")
    
    def start_attendance(self):
        if not self.student_registered:
            messagebox.showwarning("Setup Error", "Please register a student first")
            return
            
        if self.running:
            return
            
        try:
            self.video_capture = cv2.VideoCapture(0)
            if not self.video_capture.isOpened():
                raise Exception("Could not open video device")
                
            self.running = True
            self.update_video()
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to start camera: {str(e)}")
            self.stop_attendance()
    
    def stop_attendance(self):
        self.running = False
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        if hasattr(self.video_label, 'imgtk'):
            self.video_label.config(image=None)
        self.video_label.config(text="Video feed stopped")
    
    def update_video(self):
        if not self.running:
            return
            
        ret, frame = self.video_capture.read()
        if ret:
            # Convert to RGB and resize for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (640, 480))
            
            # Face recognition
            face_locations = face_recognition.face_locations(frame_rgb)
            face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces([self.known_encoding], face_encoding)

                if any(matches):
                    # Update database with attendance
                    self.cursor.execute(
                        "UPDATE students SET attendance_status = %s, timestamp = %s WHERE name = %s",
                        ("Present", datetime.now(), self.known_name)
                    )
                    self.conn.commit()

                    # Draw rectangle and text
                    cv2.rectangle(frame_rgb, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame_rgb, self.known_name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.putText(frame_rgb, self.known_age, (left, top - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.putText(frame_rgb, self.known_gender, (left, top - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.putText(frame_rgb, "Attendance Marked", (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                else:
                    cv2.rectangle(frame_rgb, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame_rgb, "Unknown", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Convert to PhotoImage
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update the label
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
        self.root.after(10, self.update_video)
    
    def on_closing(self):
        self.stop_attendance()
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()