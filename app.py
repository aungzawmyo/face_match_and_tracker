import os, threading, io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from db import init_db, connect, load_gallery, add_person, get_person_by_name, delete_person
from enroll import enroll_from_dir
from pipeline import VideoWorker

APP_TITLE = "FaceApp (CPU • Tkinter)"
MIN_W, MIN_H = 960, 640

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{MIN_W}x{MIN_H}")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # DB
        self.con = init_db()

        # Notebook (tabs)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self.people_tab = PeopleTab(self.nb, self.con)
        self.live_tab = LiveTab(self.nb, self.con)
        
        # Connect people tab to live tab for gallery refresh
        self.people_tab.set_live_tab(self.live_tab)

        self.nb.add(self.people_tab, text="People")
        self.nb.add(self.live_tab, text="Live")
        # Future: Unknowns, History, Settings

    def on_close(self):
        try:
            self.live_tab.stop_video()
        except Exception:
            pass
        self.destroy()

# -------------------- People Tab --------------------
class PeopleTab(ttk.Frame):
    def __init__(self, master, con):
        super().__init__(master)
        self.con = con
        self.live_tab = None  # Will be set by the main app
        self._build()
    
    def set_live_tab(self, live_tab):
        """Set reference to live tab for gallery refresh"""
        self.live_tab = live_tab

    def _build(self):
        self.columnconfigure(1, weight=1)
        # Left: list of people
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="nsw", padx=8, pady=8)
        ttk.Label(left, text="People").pack(anchor="w")
        self.people_list = tk.Listbox(left, width=28, height=25)
        self.people_list.pack(fill="y", expand=False)
        btns = ttk.Frame(left); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Refresh", command=self.refresh).pack(side="left", padx=2)
        ttk.Button(btns, text="Delete", command=self.delete_person).pack(side="left", padx=2)

        # Right: controls
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        right.columnconfigure(1, weight=1)

        ttk.Label(right, text="Add / Enroll Person").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(right, text="Name:").grid(row=1, column=0, sticky="e", pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=4)

        self.dir_var = tk.StringVar(value="")
        ttk.Label(right, text="Images Folder (>=5):").grid(row=2, column=0, sticky="e", pady=4)
        row2 = ttk.Frame(right); row2.grid(row=2, column=1, sticky="ew", pady=4)
        row2.columnconfigure(0, weight=1)
        ttk.Entry(row2, textvariable=self.dir_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(row2, text="Browse...", command=self.pick_dir).grid(row=0, column=1, padx=4)

        ttk.Button(right, text="Extract & Enroll", command=self.enroll).grid(row=3, column=1, sticky="e", pady=8)

        self.status = tk.StringVar(value="Ready")
        ttk.Label(right, textvariable=self.status).grid(row=4, column=0, columnspan=2, sticky="w", pady=8)

        self.refresh()

    def pick_dir(self):
        d = filedialog.askdirectory(title="Select person's images folder")
        if d:
            self.dir_var.set(d)

    def enroll(self):
        name = self.name_var.get().strip()
        img_dir = self.dir_var.get().strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter a name.")
            return
        if not os.path.isdir(img_dir):
            messagebox.showwarning("Folder required", "Please pick a valid images folder.")
            return

        def task():
            try:
                self.status.set("Extracting embeddings... (CPU)")
                enroll_from_dir(name, img_dir, con=self.con)
                self.status.set(f"Enrolled {name}.")
                self.refresh()
                # Also refresh the live video worker's gallery
                if self.live_tab and self.live_tab.worker:
                    self.live_tab.worker.refresh_gallery()
            except SystemExit as e:
                self.status.set(str(e))
            except Exception as e:
                self.status.set(f"Error: {e}")

        threading.Thread(target=task, daemon=True).start()

    def refresh(self):
        self.people_list.delete(0, tk.END)
        names = []
        for name in sorted(load_gallery(self.con).keys()):
            names.append(name)
        for n in names:
            self.people_list.insert(tk.END, n)
        # Also refresh the live video worker's gallery
        if self.live_tab and self.live_tab.worker:
            self.live_tab.worker.refresh_gallery()

    def delete_person(self):
        sel = self.people_list.curselection()
        if not sel:
            return
        name = self.people_list.get(sel[0])
        if not messagebox.askyesno("Confirm", f"Delete {name}? (embeddings too)"):
            return
        row = get_person_by_name(self.con, name)
        if row:
            delete_person(self.con, row[0])
            self.refresh()

# -------------------- Live Tab --------------------
class LiveTab(ttk.Frame):
    def __init__(self, master, con):
        super().__init__(master)
        self.con = con
        self.worker = None
        self.imgtk = None
        self._build()

    def _build(self):
        top = ttk.Frame(self); top.pack(fill="x")
        ttk.Label(top, text="Video Source:").pack(side="left", padx=4)
        self.src_var = tk.StringVar(value="0")
        src_entry = ttk.Entry(top, textvariable=self.src_var, width=12)
        src_entry.pack(side="left")
        ttk.Button(top, text="Detect Cameras", command=self.detect_cameras).pack(side="left", padx=2)
        ttk.Button(top, text="Start", command=self.start_video).pack(side="left", padx=4)
        ttk.Button(top, text="Stop", command=self.stop_video).pack(side="left", padx=4)

        self.stats_var = tk.StringVar(value="FPS: 0.0 | Known: 0 | Unknown: 0 | Tracks: 0")
        ttk.Label(self, textvariable=self.stats_var).pack(anchor="w", padx=6, pady=4)

        self.canvas = tk.Label(self)
        self.canvas.pack(fill="both", expand=True)

    def detect_cameras(self):
        """Detect available camera indices and update the interface"""
        available_cameras = []
        for i in range(5):  # Check first 5 camera indices
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    available_cameras.append(str(i))
                cap.release()
        
        if available_cameras:
            message = f"Available cameras: {', '.join(available_cameras)}"
            self.src_var.set(available_cameras[0])  # Set to first available
        else:
            message = "No cameras detected"
        
        # Show result in stats
        self.stats_var.set(message)

    def start_video(self):
        if self.worker:
            return
        src_text = self.src_var.get().strip()
        try:
            src = int(src_text)
        except ValueError:
            src = src_text  # treat as path/RTSP
        
        # Validate camera index if it's an integer
        if isinstance(src, int):
            # Test if camera can be opened
            test_cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
            if not test_cap.isOpened():
                self.stats_var.set(f"Error: Camera {src} not available")
                test_cap.release()
                return
            test_cap.release()
        
        self.worker = VideoWorker(self.con, video_src=src, on_frame=self.on_frame, on_stats=self.on_stats)
        self.worker.start()

    def stop_video(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
            
    def refresh_gallery(self):
        """Manually refresh the video worker's gallery"""
        if self.worker:
            self.worker.refresh_gallery()

    def on_frame(self, frame_bgr):
        # Convert to RGB and resize to fit label
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        # Keep it manageable
        max_w = 960
        if w > max_w:
            scale = max_w / w
            new_size = (int(w*scale), int(h*scale))
            rgb = cv2.resize(rgb, new_size, interpolation=cv2.INTER_AREA)
        im = Image.fromarray(rgb)
        self.imgtk = ImageTk.PhotoImage(image=im)
        # must set image on UI thread
        def update():
            self.canvas.configure(image=self.imgtk)
            self.canvas.image = self.imgtk
        self.after(0, update)

    def on_stats(self, stats):
        self.stats_var.set(f"FPS: {stats.get('fps',0):.1f} | Known: {stats.get('known',0)} | Unknown: {stats.get('unknown',0)} | Tracks: {stats.get('tracks',0)}")

    def stop(self):
        self.stop_video()

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
