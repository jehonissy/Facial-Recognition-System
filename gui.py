"""
gui.py
======
A minimal Tkinter GUI wrapping the same functionality as main.py, for
people who prefer clicking buttons over the command line.

Run with:  python gui.py
"""

import logging
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import utils
import enroll
import recognize
from attendance import AttendanceLogger

logger = logging.getLogger(__name__)


class FacialRecognitionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facial Recognition System")
        self.root.geometry("360x280")
        self.root.resizable(False, False)

        title = tk.Label(root, text="Facial Recognition System", font=("Segoe UI", 14, "bold"))
        title.pack(pady=(20, 10))

        button_opts = {"width": 28, "height": 2}

        tk.Button(root, text="Enroll Person", command=self.on_enroll, **button_opts).pack(pady=6)
        tk.Button(root, text="Start Recognition", command=self.on_run, **button_opts).pack(pady=6)
        tk.Button(root, text="Start Recognition (+ Attendance)",
                  command=self.on_run_attendance, **button_opts).pack(pady=6)
        tk.Button(root, text="View Attendance", command=self.on_view_attendance, **button_opts).pack(pady=6)
        tk.Button(root, text="Exit", command=root.quit, **button_opts).pack(pady=6)

        self.status = tk.Label(root, text="Ready.", fg="gray")
        self.status.pack(pady=(10, 0))

    def set_status(self, text: str):
        self.status.config(text=text)
        self.root.update_idletasks()

    def _run_in_background(self, target, *args):
        """Run a blocking operation (webcam loop) in a thread so the GUI
        doesn't freeze while OpenCV owns the video window.
        """
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()

    def on_enroll(self):
        name = simpledialog.askstring("Enroll Person", "Enter the person's name:")
        if not name:
            return
        self.set_status(f"Enrolling '{name}'... look at the webcam window.")

        def task():
            try:
                count = enroll.enroll_from_webcam(name)
                self.set_status(f"Enrolled '{name}' with {count} image(s).")
                messagebox.showinfo("Enrollment complete", f"Enrolled '{name}' with {count} image(s).")
            except enroll.EnrollmentError as e:
                self.set_status("Enrollment failed.")
                messagebox.showerror("Enrollment failed", str(e))

        self._run_in_background(task)

    def on_run(self):
        self.set_status("Recognition running... press 'q' in the video window to stop.")
        self._run_in_background(lambda: recognize.run(attendance=False))

    def on_run_attendance(self):
        self.set_status("Recognition + attendance running... press 'q' in the video window to stop.")
        self._run_in_background(lambda: recognize.run(attendance=True))

    def on_view_attendance(self):
        rows = AttendanceLogger().read_all()
        if not rows:
            messagebox.showinfo("Attendance", "No attendance records yet.")
            return

        window = tk.Toplevel(self.root)
        window.title("Attendance Records")
        window.geometry("400x300")

        tree = ttk.Treeview(window, columns=("Name", "Date", "Time"), show="headings")
        for col in ("Name", "Date", "Time"):
            tree.heading(col, text=col)
            tree.column(col, width=120)
        for row in rows:
            tree.insert("", tk.END, values=(row.get("Name"), row.get("Date"), row.get("Time")))
        tree.pack(fill=tk.BOTH, expand=True)


def main():
    utils.ensure_project_dirs()
    utils.setup_logging()

    root = tk.Tk()
    FacialRecognitionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
