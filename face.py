import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import datetime

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Attendance System")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f4f7")

        self.photo_path = None
        self.clock_label = None

        self.create_widgets()

    def create_widgets(self):
        # Header
        header = tk.Label(self.root, text="Smart Attendance System", font=("Helvetica", 24, "bold"), bg="#2c3e50", fg="white", pady=10)
        header.pack(fill=tk.X)

        # Clock
        self.clock_label = tk.Label(self.root, font=("Helvetica", 12), bg="#f0f4f7", fg="#34495e")
        self.clock_label.pack(pady=5)
        self.update_clock()

        # Main frame
        frame = tk.Frame(self.root, bg="white", padx=20, pady=20)
        frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Input Fields
        ttk.Label(frame, text="Student Name:", font=("Helvetica", 12)).grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Roll Number:", font=("Helvetica", 12)).grid(row=1, column=0, sticky="w", pady=5)
        self.roll_entry = ttk.Entry(frame, width=30)
        self.roll_entry.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Upload Photo:", font=("Helvetica", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.upload_btn = ttk.Button(frame, text="Choose File", command=self.upload_photo)
        self.upload_btn.grid(row=2, column=1, pady=5, sticky="w")

        self.image_label = tk.Label(frame, bg="white")
        self.image_label.grid(row=0, column=2, rowspan=4, padx=20)

        # Buttons
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.grid(row=4, column=0, columnspan=3, pady=15)

        self.mark_btn = ttk.Button(btn_frame, text="Mark Attendance", command=self.mark_attendance)
        self.mark_btn.grid(row=0, column=0, padx=10)

        self.clear_btn = ttk.Button(btn_frame, text="Clear Fields", command=self.clear_fields)
        self.clear_btn.grid(row=0, column=1, padx=10)

        # Status Label
        self.status_label = tk.Label(self.root, text="Status: Waiting for input", font=("Helvetica", 12), bg="#f0f4f7", fg="gray")
        self.status_label.pack(pady=10)

    def update_clock(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.configure(text=f"Current Time: {now}")
        self.root.after(1000, self.update_clock)

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.photo_path = file_path
            image = Image.open(file_path)
            image = image.resize((100, 100))
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
            self.status_label.configure(text="Status: Photo uploaded ✅", fg="green")

    def mark_attendance(self):
        name = self.name_entry.get()
        roll = self.roll_entry.get()
        if not name or not roll or not self.photo_path:
            messagebox.showerror("Missing Fields", "Please complete all fields and upload a photo.")
            self.status_label.configure(text="Status: Missing input ❌", fg="red")
            return
        # Simulate attendance marking
        self.status_label.configure(text=f"Attendance marked for {name} (Roll: {roll}) ✅", fg="green")
        messagebox.showinfo("Success", f"Attendance marked for {name}!")

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.roll_entry.delete(0, tk.END)
        self.image_label.configure(image="")
        self.image_label.image = None
        self.photo_path = None
        self.status_label.configure(text="Status: Fields cleared", fg="gray")


if __name__ == '__main__':
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()
