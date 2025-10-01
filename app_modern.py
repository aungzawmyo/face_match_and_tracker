import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import logging

# Handle zoneinfo import for PyInstaller compatibility
try:
    import zoneinfo
except ImportError:
    try:
        from backports import zoneinfo
    except ImportError:
        # Create a mock zoneinfo module to prevent import errors
        import sys
        import types
        zoneinfo = types.ModuleType('zoneinfo')
        zoneinfo.ZoneInfo = lambda x: None
        zoneinfo.ZoneInfoNotFoundError = Exception
        sys.modules['zoneinfo'] = zoneinfo

# Configure logging
log_file = os.path.join(os.getcwd(), 'facescanner.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),  # 'w' mode to create fresh log each time
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log startup immediately
logger.info(f"FaceScannerPro starting up - Log file: {log_file}")
logger.info(f"Working directory: {os.getcwd()}")

from db import init_db, connect, load_gallery, add_person, get_person_by_name, get_person_by_name_legacy, get_person_by_id, update_person, delete_person
from enroll import enroll_from_dir
from pipeline import VideoWorker

APP_TITLE = "FaceScannerPro - Advanced Face Recognition System"
MIN_W, MIN_H = 1366, 768  # Optimized for minimum screen size

# Modern color scheme - Enhanced with gradients and shadows
COLORS = {
    'primary': '#1A202C',      # Deep dark blue
    'secondary': '#4299E1',     # Modern blue
    'success': '#38A169',       # Fresh green
    'danger': '#E53E3E',        # Clean red
    'warning': '#DD6B20',       # Modern orange
    'info': '#3182CE',          # Information blue
    'light': '#F7FAFC',         # Very light gray
    'dark': '#2D3748',          # Dark gray
    'white': '#FFFFFF',
    'background': '#EDF2F7',    # Modern light background
    'card': '#FFFFFF',          # Pure white cards
    'text': '#1A202C',          # Dark text
    'text_light': '#718096',    # Light text
    'border': '#E2E8F0',        # Subtle border
    'hover': '#EDF2F7',         # Hover effect
    'accent': '#805AD5',        # Purple accent
    'sidebar': '#F8F9FA',       # Sidebar background
    'header_gradient_start': '#667EEA',  # Gradient start
    'header_gradient_end': '#764BA2',    # Gradient end
}

class ModernStyle:
    @staticmethod
    def configure_styles():
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme as base
        
        # Configure modern button styles with better spacing
        style.configure('Modern.TButton', 
                       font=('Segoe UI', 10), 
                       padding=(20, 10),
                       relief='flat',
                       borderwidth=0)
        
        # Primary button with hover effect
        style.configure('Primary.TButton',
                       background=COLORS['secondary'],
                       foreground=COLORS['white'],
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 12),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Primary.TButton',
                 background=[('active', COLORS['info']),
                           ('pressed', COLORS['dark'])])
        
        # Success button
        style.configure('Success.TButton',
                       background=COLORS['success'],
                       foreground=COLORS['white'],
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 12),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Success.TButton',
                 background=[('active', '#2F855A'),
                           ('pressed', '#276749')])
        
        # Danger button
        style.configure('Danger.TButton',
                       background=COLORS['danger'],
                       foreground=COLORS['white'],
                       font=('Segoe UI', 11, 'bold'),
                       padding=(20, 12),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Danger.TButton',
                 background=[('active', '#C53030'),
                           ('pressed', '#9B2C2C')])
        
        # Modern notebook style - Same size for active and inactive tabs
        style.configure('Modern.TNotebook',
                       tabposition='n',
                       borderwidth=0)
        
        style.configure('Modern.TNotebook.Tab',
                       padding=(16, 8),  # Fixed padding for all states
                       font=('Segoe UI', 10, 'normal'),  # Fixed font for all states
                       borderwidth=0,
                       width=22)  # Fixed width to ensure same size
        
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', COLORS['primary']),      # Active: dark background
                           ('!selected', COLORS['light'])],        # Inactive: light background
                 foreground=[('selected', COLORS['white']),        # Active: white text
                           ('!selected', COLORS['text_light'])],   # Inactive: light gray text
                 padding=[('selected', (16, 8)),                  # Same padding for active
                         ('!selected', (16, 8))],                 # Same padding for inactive
                 font=[('selected', ('Segoe UI', 10, 'normal')),  # Same font for active
                      ('!selected', ('Segoe UI', 10, 'normal'))])  # Same font for inactive

    @staticmethod
    def bind_mousewheel(widget, canvas):
        """Bind mouse wheel scrolling to canvas"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        widget.bind('<Enter>', _bind_to_mousewheel)
        widget.bind('<Leave>', _unbind_from_mousewheel)

class App(tk.Tk):
    def __init__(self):
        logger.info("Initializing FaceScannerPro Application")
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{MIN_W}x{MIN_H}")
        self.configure(bg=COLORS['background'])
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configure modern styles
        ModernStyle.configure_styles()
        
        # DB
        try:
            logger.info("Initializing database...")
            self.con = init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")
            self.destroy()
            return
        
        # Create modern interface
        try:
            logger.info("Creating user interface...")
            self.create_modern_interface()
            logger.info("User interface created successfully")
        except Exception as e:
            logger.error(f"Failed to create interface: {e}")
            messagebox.showerror("Interface Error", f"Failed to create interface: {e}")
            self.destroy()
            return
        
        logger.info("FaceScannerPro Application initialized successfully")
        
    def create_modern_interface(self):
        # Main container with reduced padding for smaller screens
        main_container = tk.Frame(self, bg=COLORS['background'])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(main_container)
        
        # Content area with notebook
        self.create_content_area(main_container)
        
    def create_header(self, parent):
        # Compact modern header optimized for smaller screens
        header_frame = tk.Frame(parent, bg=COLORS['header_gradient_start'], height=50)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Main content container with reduced padding
        content_frame = tk.Frame(header_frame, bg=COLORS['header_gradient_start'])
        content_frame.pack(fill="both", expand=True, padx=20, pady=8)
        
        # Left side - Compact title
        left_frame = tk.Frame(content_frame, bg=COLORS['header_gradient_start'])
        left_frame.pack(side="left", fill="y")
        
        # Compact app title
        title_label = tk.Label(left_frame, 
                              text="🔍 FaceScannerPro",
                              font=('Segoe UI', 18, 'bold'),
                              bg=COLORS['header_gradient_start'],
                              fg=COLORS['white'])
        title_label.pack(anchor="w")
        
        # Right side - Compact status
        right_frame = tk.Frame(content_frame, bg=COLORS['header_gradient_start'])
        right_frame.pack(side="right", fill="y")
        
        # Compact status badge
        status_frame = tk.Frame(right_frame, bg=COLORS['success'], relief='flat', bd=0)
        status_frame.pack(side="top", anchor="e")
        
        status_label = tk.Label(status_frame,
                               text="● READY",
                               font=('Segoe UI', 9, 'bold'),
                               bg=COLORS['success'],
                               fg=COLORS['white'])
        status_label.pack(padx=10, pady=4)
        
    def create_content_area(self, parent):
        # Notebook with modern styling and shadow effect
        notebook_container = tk.Frame(parent, bg=COLORS['background'])
        notebook_container.pack(fill="both", expand=True)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(notebook_container, bg=COLORS['border'], height=2)
        shadow_frame.pack(fill="x")
        
        self.nb = ttk.Notebook(notebook_container, style='Modern.TNotebook')
        self.nb.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Create tabs with modern design
        self.people_tab = ModernPeopleTab(self.nb, self.con, self)  # Pass root window
        self.live_tab = ModernLiveTab(self.nb, self.con)
        self.history_tab = TrackHistoryTab(self.nb, self.con, self)  # Add track history tab
        
        # Connect tabs
        self.people_tab.set_live_tab(self.live_tab)
        
        self.nb.add(self.people_tab, text="  👥 People Management  ")
        self.nb.add(self.live_tab, text="  📹 Live Recognition  ")
        self.nb.add(self.history_tab, text="  📊 Track History  ")
        
    def on_close(self):
        try:
            self.live_tab.stop_video()
        except Exception:
            pass
        self.destroy()

class ModernPeopleTab(ttk.Frame):
    def __init__(self, master, con, root):
        super().__init__(master)
        self.con = con
        self.root = root  # Store reference to root window
        self.live_tab = None
        self.current_person_data = None  # Store current person data
        self.configure(style='Card.TFrame')
        self._build_modern_interface()

    def set_live_tab(self, live_tab):
        self.live_tab = live_tab

    def _build_modern_interface(self):
        # Main container with reduced padding for smaller screens
        main_frame = tk.Frame(self, bg=COLORS['background'])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - People list (narrower for small screens)
        self.create_people_list_panel(main_frame)
        
        # Right panel - Person details and add form
        self.create_details_panel(main_frame)
        
        # Load initial data
        self.refresh()
        
    def create_people_list_panel(self, parent):
        # Left panel with compact design for smaller screens
        left_panel = tk.Frame(parent, bg=COLORS['card'], relief='flat', bd=0, width=280)
        left_panel.pack(side="left", fill="y", padx=(0, 10), ipadx=10, ipady=10)
        left_panel.pack_propagate(False)
        
        # Add subtle shadow border
        border_frame = tk.Frame(left_panel, bg=COLORS['border'], height=1)
        border_frame.pack(fill="x", side="bottom")
        
        # Compact header
        header_frame = tk.Frame(left_panel, bg=COLORS['card'])
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Compact title
        title_label = tk.Label(header_frame,
                              text="👥 People",
                              font=('Segoe UI', 14, 'bold'),
                              bg=COLORS['card'],
                              fg=COLORS['text'])
        title_label.pack(anchor="w")
        
        # Compact count badge
        count_frame = tk.Frame(header_frame, bg=COLORS['info'])
        count_frame.pack(anchor="w", pady=(5, 0))
        
        self.count_label = tk.Label(count_frame,
                                   text="0 enrolled",
                                   font=('Segoe UI', 9, 'bold'),
                                   bg=COLORS['info'],
                                   fg=COLORS['white'])
        self.count_label.pack(padx=8, pady=3)
        
        # Compact search
        search_frame = tk.Frame(left_panel, bg=COLORS['card'])
        search_frame.pack(fill="x", pady=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame,
                               textvariable=self.search_var,
                               font=('Segoe UI', 10),
                               width=25,
                               bg=COLORS['light'],
                               fg=COLORS['text'],
                               relief='flat',
                               bd=5,
                               highlightthickness=0)
        search_entry.pack(fill="x", ipady=5)
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Compact people listbox
        list_frame = tk.Frame(left_panel, bg=COLORS['card'])
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        listbox_frame = tk.Frame(list_frame, bg=COLORS['border'], relief='flat', bd=1)
        listbox_frame.pack(fill="both", expand=True)
        
        self.people_listbox = tk.Listbox(listbox_frame,
                                        font=('Segoe UI', 10),
                                        height=15,
                                        width=28,
                                        selectmode='single',
                                        bg=COLORS['white'],
                                        fg=COLORS['text'],
                                        selectbackground=COLORS['secondary'],
                                        selectforeground=COLORS['white'],
                                        relief='flat',
                                        bd=0,
                                        highlightthickness=0,
                                        activestyle='none')
        
        scrollbar = tk.Scrollbar(listbox_frame, 
                                orient="vertical", 
                                command=self.people_listbox.yview,
                                bg=COLORS['light'],
                                troughcolor=COLORS['background'],
                                borderwidth=0,
                                highlightthickness=0,
                                width=10)
        
        self.people_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.people_listbox.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        scrollbar.pack(side="right", fill="y")
        
        ModernStyle.bind_mousewheel(listbox_frame, self.people_listbox)
        self.people_listbox.bind('<<ListboxSelect>>', self.on_person_select)
        
        # Compact action buttons
        button_frame = tk.Frame(left_panel, bg=COLORS['card'])
        button_frame.pack(fill="x")
        
        # Action buttons with labels - arranged vertically for better space usage
        refresh_btn = tk.Button(button_frame,
                               text="🔄 Refresh",
                               command=self.refresh,
                               bg=COLORS['info'],
                               fg=COLORS['white'],
                               font=('Segoe UI', 9, 'bold'),
                               relief='flat',
                               bd=0,
                               pady=6,
                               cursor='hand2')
        refresh_btn.pack(fill="x", pady=(0, 3))
        
        edit_btn = tk.Button(button_frame,
                            text="✏️ Edit Selected",
                            command=self.edit_person,
                            bg=COLORS['warning'],
                            fg=COLORS['white'],
                            font=('Segoe UI', 9, 'bold'),
                            relief='flat',
                            bd=0,
                            pady=6,
                            cursor='hand2')
        edit_btn.pack(fill="x", pady=(0, 3))
        
        delete_btn = tk.Button(button_frame,
                              text="🗑️ Delete Selected",
                              command=self.delete_person,
                              bg=COLORS['danger'],
                              fg=COLORS['white'],
                              font=('Segoe UI', 9, 'bold'),
                              relief='flat',
                              bd=0,
                              pady=6,
                              cursor='hand2')
        delete_btn.pack(fill="x")
        
        # Add hover effects
        self.add_button_hover_effect(refresh_btn, COLORS['info'], '#2B77A8')
        self.add_button_hover_effect(edit_btn, COLORS['warning'], '#B7791F')
        self.add_button_hover_effect(delete_btn, COLORS['danger'], '#C53030')
        
    def add_button_hover_effect(self, button, normal_color, hover_color):
        """Add hover effect to buttons"""
        def on_enter(e):
            button.config(bg=hover_color)
        
        def on_leave(e):
            button.config(bg=normal_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def create_details_panel(self, parent):
        # Right panel
        right_panel = tk.Frame(parent, bg=COLORS['background'])
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Create notebook for details and add person
        self.details_nb = ttk.Notebook(right_panel)
        self.details_nb.pack(fill="both", expand=True)
        
        # Person details tab
        self.details_frame = tk.Frame(self.details_nb, bg=COLORS['card'])
        self.details_nb.add(self.details_frame, text="  👤 Person Details  ")
        
        # Add person tab
        self.add_frame = tk.Frame(self.details_nb, bg=COLORS['card'])
        self.details_nb.add(self.add_frame, text="  ➕ Add New Person  ")
        
        # Build details view
        self.build_details_view()
        
        # Build add person form
        self.build_add_person_form()
        
    def build_details_view(self):
        # Details container with compact padding
        details_container = tk.Frame(self.details_frame, bg=COLORS['card'])
        details_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Default message
        self.no_selection_frame = tk.Frame(details_container, bg=COLORS['card'])
        self.no_selection_frame.pack(fill="both", expand=True)
        
        no_selection_label = tk.Label(self.no_selection_frame,
                                     text="👤\n\nSelect a person from the list\nto view their details",
                                     font=('Segoe UI', 14),
                                     bg=COLORS['card'],
                                     fg=COLORS['text_light'],
                                     justify='center')
        no_selection_label.pack(expand=True)
        
        # Person details frame (hidden initially)
        self.person_details_frame = tk.Frame(details_container, bg=COLORS['card'])
        
    def build_add_person_form(self):
        # Add person container with compact padding
        add_container = tk.Frame(self.add_frame, bg=COLORS['card'])
        add_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Form frame (removed header to save space)
        form_frame = tk.Frame(add_container, bg=COLORS['card'])
        form_frame.pack(fill="x", pady=(0, 10))
        
        # Configure grid
        form_frame.columnconfigure(1, weight=1)
        
        # Form fields
        fields = [
            ("Full Name *", "name_var"),
            ("Phone Number", "phone_var"),
            ("Date of Birth", "dob_var"),
            ("Website/Link", "link_var"),
            ("Social Media", "social_link_var"),
            ("General Info", "info_var"),
            ("Additional Info", "info1_var"),
            ("Notes", "note_var")
        ]
        
        self.form_vars = {}
        
        for row, (label_text, var_name) in enumerate(fields):
            # Label
            label = tk.Label(form_frame,
                           text=label_text,
                           font=('Segoe UI', 10, 'bold'),
                           bg=COLORS['card'],
                           fg=COLORS['text'])
            label.grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=3)
            
            # Entry or Text widget
            var = tk.StringVar()
            self.form_vars[var_name] = var
            
            if var_name in ['info_var', 'info1_var', 'note_var']:
                # Smaller text widget for longer content
                text_widget = tk.Text(form_frame,
                                    height=2,
                                    font=('Segoe UI', 9),
                                    bg=COLORS['white'],
                                    fg=COLORS['text'],
                                    relief='solid',
                                    bd=1,
                                    wrap='word')
                text_widget.grid(row=row, column=1, sticky="ew", pady=2)
                setattr(self, var_name.replace('_var', '_text'), text_widget)
            else:
                # Smaller entry widget
                entry = tk.Entry(form_frame,
                               textvariable=var,
                               font=('Segoe UI', 10),
                               bg=COLORS['white'],
                               fg=COLORS['text'],
                               relief='solid',
                               bd=1)
                entry.grid(row=row, column=1, sticky="ew", pady=2, ipady=2)
        
        # Training Images folder section - compact single row
        images_frame = tk.Frame(add_container, bg=COLORS['card'])
        images_frame.pack(fill="x", pady=(5, 15))
        images_frame.columnconfigure(1, weight=1)
        
        # Label, Entry, and Browse button all in one row
        images_label = tk.Label(images_frame,
                               text="Training Images Folder *",
                               font=('Segoe UI', 10, 'bold'),
                               bg=COLORS['card'],
                               fg=COLORS['text'])
        images_label.grid(row=0, column=0, sticky="w", padx=(0, 10), pady=2)
        
        self.dir_var = tk.StringVar()
        dir_entry = tk.Entry(images_frame,
                           textvariable=self.dir_var,
                           font=('Segoe UI', 10),
                           bg=COLORS['white'],
                           fg=COLORS['text'],
                           relief='solid',
                           bd=1)
        dir_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=2, ipady=2)
        
        browse_btn = tk.Button(images_frame,
                             text="📁 Browse",
                             command=self.pick_dir,
                             bg=COLORS['secondary'],
                             fg=COLORS['white'],
                             font=('Segoe UI', 9, 'bold'),
                             relief='flat',
                             padx=12,
                             pady=4)
        browse_btn.grid(row=0, column=2)
        
        # Compact help text
        help_label = tk.Label(images_frame,
                             text="Select folder with 5+ clear face photos",
                             font=('Segoe UI', 8),
                             bg=COLORS['card'],
                             fg=COLORS['text_light'])
        help_label.grid(row=1, column=1, sticky="w", pady=(3, 0))
        
        # Action buttons - more compact
        action_frame = tk.Frame(add_container, bg=COLORS['card'])
        action_frame.pack(fill="x", pady=(10, 0))
        
        enroll_btn = tk.Button(action_frame,
                             text="🚀 Extract & Enroll Person",
                             command=self.enroll,
                             bg=COLORS['success'],
                             fg=COLORS['white'],
                             font=('Segoe UI', 10, 'bold'),
                             relief='flat',
                             padx=15,
                             pady=6)
        enroll_btn.pack(side="right")
        
        clear_btn = tk.Button(action_frame,
                            text="🗑️ Clear Form",
                            command=self.clear_form,
                            bg=COLORS['warning'],
                            fg=COLORS['white'],
                            font=('Segoe UI', 9, 'bold'),
                            relief='flat',
                            padx=12,
                            pady=6)
        clear_btn.pack(side="right", padx=(0, 8))
        
        # Status - more compact
        self.status_var = tk.StringVar(value="Ready to add new person")
        status_label = tk.Label(add_container,
                               textvariable=self.status_var,
                               font=('Segoe UI', 9),
                               bg=COLORS['card'],
                               fg=COLORS['info'])
        status_label.pack(anchor="w", pady=(8, 0))

    def pick_dir(self):
        d = filedialog.askdirectory(title="Select person's images folder")
        if d:
            self.dir_var.set(d)

    def clear_form(self):
        # Clear all form variables
        for var in self.form_vars.values():
            var.set("")
        
        # Clear text widgets
        for attr_name in ['info_text', 'info1_text', 'note_text']:
            if hasattr(self, attr_name):
                text_widget = getattr(self, attr_name)
                text_widget.delete('1.0', tk.END)
        
        self.dir_var.set("")
        self.status_var.set("Form cleared - Ready to add new person")

    def get_text_widget_content(self, widget):
        return widget.get('1.0', tk.END).strip()

    def enroll(self):
        name = self.form_vars['name_var'].get().strip()
        phone = self.form_vars['phone_var'].get().strip()
        dob = self.form_vars['dob_var'].get().strip()
        link = self.form_vars['link_var'].get().strip()
        social_link = self.form_vars['social_link_var'].get().strip()
        img_dir = self.dir_var.get().strip()
        
        # Get text widget content
        info = self.get_text_widget_content(self.info_text)
        info1 = self.get_text_widget_content(self.info1_text)
        note = self.get_text_widget_content(self.note_text)
        
        if not name:
            messagebox.showwarning("Name Required", "Please enter the person's full name.")
            return
        if not os.path.isdir(img_dir):
            messagebox.showwarning("Images Folder Required", "Please select a valid images folder.")
            return

        def task():
            try:
                logger.info("add person is working.........")

                self.status_var.set("🔄 Extracting face embeddings...")
                
                # Check if person already exists
                existing = get_person_by_name_legacy(self.con, name)
                if existing:
                    logger.info("add person is existing.........")

                    person_id = existing[0]
                    update_person(self.con, person_id, name, phone, dob, link, info, social_link, info1, note)
                else:
                    logger.info("add person is add_person.........")

                    # Fix: Use keyword arguments to avoid parameter shift issue
                    person_id = add_person(self.con, name, None, 
                                         phone=phone, dob=dob, link=link, 
                                         info=info, social_link=social_link, 
                                         info1=info1, note=note)
                
                # Enroll face embeddings
                enroll_from_dir(name, img_dir, con=self.con)
                
                self.status_var.set(f"✅ Successfully enrolled {name}!")
                self.refresh()
                self.clear_form()
                
                # Refresh live video gallery
                if self.live_tab and self.live_tab.worker:
                    self.live_tab.worker.refresh_gallery()
                    
            except SystemExit as e:
                self.status_var.set(f"❌ Error..: {e}")
            except Exception as e:
                self.status_var.set(f"❌ Error---: {e}")

        threading.Thread(target=task, daemon=True).start()

    def on_search(self, event=None):
        search_term = self.search_var.get().lower()
        self.people_listbox.delete(0, tk.END)
        
        gallery = load_gallery(self.con)
        filtered_names = [name for name in sorted(gallery.keys()) if search_term in name.lower()]
        
        for name in filtered_names:
            self.people_listbox.insert(tk.END, name)
        
        self.count_label.config(text=f"{len(filtered_names)} people found")

    def on_person_select(self, event=None):
        selection = self.people_listbox.curselection()
        if not selection:
            return
            
        name = self.people_listbox.get(selection[0])
        # Use the new get_person_by_name function that handles its own connection
        person_data = get_person_by_name(name)
        
        if person_data:
            self.current_person_data = person_data  # Store current person data
            self.show_person_details(person_data)
            # Switch to details tab
            self.details_nb.select(0)

    def show_person_details(self, person_data):
        # Hide no selection frame
        self.no_selection_frame.pack_forget()
        
        # Clear previous details
        for widget in self.person_details_frame.winfo_children():
            widget.destroy()
        
        # Show person details frame
        self.person_details_frame.pack(fill="both", expand=True)
        
        # Create scrollable details view
        self.create_person_detail_view(self.person_details_frame, person_data)

    def create_person_detail_view(self, parent, person_data):
        # Create scrollable content for person details
        canvas = tk.Canvas(parent, bg=COLORS['card'], highlightthickness=0, height=500)
        scrollbar_detail = tk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                                      bg=COLORS['light'], troughcolor=COLORS['background'],
                                      borderwidth=0, highlightthickness=0, width=10)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['card'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_detail.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_detail.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas
        ModernStyle.bind_mousewheel(canvas, canvas)
        
        # Header with person name
        header_frame = tk.Frame(scrollable_frame, bg=COLORS['primary'])
        header_frame.pack(fill="x", pady=(0, 20))
        
        name_label = tk.Label(header_frame,
                             text=person_data['name'],
                             font=('Segoe UI', 18, 'bold'),
                             bg=COLORS['primary'],
                             fg=COLORS['white'])
        name_label.pack(pady=15)
        
        # Main content container - responsive layout
        main_content = tk.Frame(scrollable_frame, bg=COLORS['card'])
        main_content.pack(fill="both", expand=True, padx=20)

        # # Basic info section
        # basic_section = tk.Frame(scrollable_frame, bg=COLORS['card'])
        # basic_section.pack(fill="x", pady=(0, 1))
        
        # Basic info section - use grid for better space utilization
        basic_section = tk.Frame(main_content, bg=COLORS['card'])
        basic_section.pack(fill="x", pady=(0, 25))
        
        basic_header = tk.Label(basic_section,
                           text="ℹ️ Basic Information",
                           font=('Segoe UI', 16, 'bold'),
                           bg=COLORS['card'],
                           fg=COLORS['text'])
        basic_header.pack(anchor="w", pady=(0, 15))
        
        # Basic info container with responsive grid
        basic_container = tk.Frame(basic_section, bg=COLORS['light'], relief='flat', bd=1)
        basic_container.pack(fill="x", pady=(0, 10))
        
        # Configure grid columns to be responsive
        basic_container.columnconfigure(0, weight=1, minsize=120)
        basic_container.columnconfigure(1, weight=2, minsize=200)
        basic_container.columnconfigure(2, weight=1, minsize=120)
        basic_container.columnconfigure(3, weight=2, minsize=200)
        
        # Create info display fields in a 2x2 grid for better space usage
        info_fields = [
            ("ID:", str(person_data['id'])),
            ("Name:", person_data['name']),
            ("Phone:", person_data.get('phone', 'Not provided')),
            ("Date of Birth:", person_data.get('dob', 'Not provided')),
        ]
        
        for i, (label, value) in enumerate(info_fields):
            row = i // 2
            col = (i % 2) * 2
            
            # Label
            label_widget = tk.Label(basic_container,
                                text=label,
                                font=('Segoe UI', 11, 'bold'),
                                bg=COLORS['light'],
                                fg=COLORS['text'],
                                anchor='w')
            label_widget.grid(row=row, column=col, sticky="w", padx=(15, 5), pady=12)
            
            # Value
            value_widget = tk.Label(basic_container,
                                text=value or 'Not provided',
                                font=('Segoe UI', 11),
                                bg=COLORS['light'],
                                fg=COLORS['text'],
                                anchor='w',
                                wraplength=180)
            value_widget.grid(row=row, column=col+1, sticky="ew", padx=(0, 15), pady=12)
        
        # Additional info section - use full width efficiently
        additional_section = tk.Frame(main_content, bg=COLORS['card'])
        additional_section.pack(fill="x", pady=(0, 20))
        
        additional_header = tk.Label(additional_section,
                                text="📝 Additional Information",
                                font=('Segoe UI', 16, 'bold'),
                                bg=COLORS['card'],
                                fg=COLORS['text'])
        additional_header.pack(anchor="w", pady=(0, 15))
        
        # Additional info container with better layout
        additional_container = tk.Frame(additional_section, bg=COLORS['light'], relief='flat', bd=1)
        additional_container.pack(fill="x")
        
        # Configure column weights for responsive design
        additional_container.columnconfigure(1, weight=1)
        
        additional_fields = [
            ("Link:", person_data.get('link', '')),
            ("Social Link:", person_data.get('social_link', '')),
            ("Info:", person_data.get('info', '')),
            ("Info1:", person_data.get('info1', '')),
            ("Note:", person_data.get('note', '')),
        ]
        
        for i, (label, value) in enumerate(additional_fields):
            # Label
            label_widget = tk.Label(additional_container,
                                text=label,
                                font=('Segoe UI', 11, 'bold'),
                                bg=COLORS['light'],
                                fg=COLORS['text'],
                                anchor='nw',
                                width=12)
            label_widget.grid(row=i, column=0, sticky="nw", padx=(15, 10), pady=12)
            
            # Value - use full available width
            display_value = value or 'Not provided'
            
            # Create appropriate widget based on content length
            if len(display_value) > 100:
                # Use Text widget for long content
                value_frame = tk.Frame(additional_container, bg=COLORS['white'])
                value_frame.grid(row=i, column=1, sticky="ew", padx=(0, 15), pady=8)
                
                value_text = tk.Text(value_frame,
                                height=3,
                                font=('Segoe UI', 10),
                                bg=COLORS['white'],
                                fg=COLORS['text'],
                                relief='flat',
                                wrap='word',
                                borderwidth=5,
                                state='normal')
                value_text.insert('1.0', display_value)
                value_text.config(state='disabled')
                value_text.pack(fill="both", expand=True)
            else:
                # Use Label for shorter content
                value_widget = tk.Label(additional_container,
                                    text=display_value,
                                    font=('Segoe UI', 10),
                                    bg=COLORS['white'],
                                    fg=COLORS['text'],
                                    anchor='nw',
                                    justify='left',
                                    wraplength=500,  # Increased wrap length for full width
                                    relief='flat',
                                    bd=5)
                value_widget.grid(row=i, column=1, sticky="ew", padx=(0, 15), pady=8)
        
        # Action buttons - centered and properly spaced
        button_frame = tk.Frame(main_content, bg=COLORS['card'])
        button_frame.pack(fill="x", pady=(20, 0))
        
        # Center the buttons
        button_container = tk.Frame(button_frame, bg=COLORS['card'])
        button_container.pack(anchor="center")
        
        edit_btn = tk.Button(button_container,
                            text="✏️ Edit Person",
                            command=self.edit_current_person,
                            bg=COLORS['warning'],
                            fg=COLORS['white'],
                            font=('Segoe UI', 12, 'bold'),
                            relief='flat',
                            bd=0,
                            padx=25,
                            pady=10,
                            cursor='hand2',
                            width=15)
        edit_btn.pack(side="left", padx=(0, 15))
        
        delete_btn = tk.Button(button_container,
                            text="🗑️ Delete Person",
                            command=self.delete_current_person,
                            bg=COLORS['danger'],
                            fg=COLORS['white'],
                            font=('Segoe UI', 12, 'bold'),
                            relief='flat',
                            bd=0,
                            padx=25,
                            pady=10,
                            cursor='hand2',
                            width=15)
        delete_btn.pack(side="right")
        
        # Add hover effects
        self.add_button_hover_effect(edit_btn, COLORS['warning'], '#B7791F')
        self.add_button_hover_effect(delete_btn, COLORS['danger'], '#C53030')
        
        # Configure canvas window width to use full available space
        def configure_canvas_width(event):
            canvas_width = event.width - scrollbar_detail.winfo_width()
            canvas.itemconfig(canvas.find_all()[0], width=canvas_width)
        
        canvas.bind('<Configure>', configure_canvas_width)

    def edit_current_person(self):
        """Edit the currently selected person"""
        if self.current_person_data:
            self.open_edit_dialog(self.current_person_data)
        else:
            messagebox.showwarning("No Selection", "Please select a person to edit")
    
    def delete_current_person(self):
        """Delete the currently selected person"""
        if self.current_person_data:
            result = messagebox.askyesno("Confirm Delete", 
                                       f"Are you sure you want to delete {self.current_person_data['name']}?\n\nThis action cannot be undone.")
            if result:
                try:
                    delete_person(self.con, self.current_person_data['id'])
                    self.refresh()
                    # Hide details
                    self.person_details_frame.pack_forget()
                    self.no_selection_frame.pack(fill="both", expand=True)
                    self.current_person_data = None
                    messagebox.showinfo("Success", "Person deleted successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete person: {str(e)}")
        else:
            messagebox.showwarning("No Selection", "Please select a person to delete")

    def refresh(self):
        if not self.con:
            logger.warning("Database connection is closed.")
            return
    
        
        self.people_listbox.delete(0, tk.END)
        gallery = load_gallery(self.con)
        names = sorted(gallery.keys())
        
        for name in names:
            self.people_listbox.insert(tk.END, name)
        
        self.count_label.config(text=f"{len(names)} enrolled")
        
        # Clear search
        self.search_var.set("")
        
        # Refresh live video gallery
        if self.live_tab and self.live_tab.worker:
            self.live_tab.worker.refresh_gallery()

    def edit_person(self):
        """Open edit dialog for selected person"""
        selection = self.people_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a person to edit")
            return
            
        selected_name = self.people_listbox.get(selection[0])
        person_data = self.get_person_data(selected_name)
        
        if not person_data:
            messagebox.showerror("Error", "Could not load person data")
            return
            
        self.open_edit_dialog(person_data)
    
    def open_edit_dialog(self, person_data):
        """Open the edit person dialog"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Person - {person_data['name']}")
        edit_window.geometry("650x800")  # Made even taller
        edit_window.configure(bg=COLORS['card'])
        edit_window.resizable(True, True)  # Allow resizing for better UX
        
        # Center the window
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Center window on screen
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (650 // 2)
        y = (edit_window.winfo_screenheight() // 2) - (800 // 2)
        edit_window.geometry(f"650x800+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(edit_window, bg=COLORS['primary'])
        header_frame.pack(fill="x", pady=(0, 15))
        
        header_label = tk.Label(header_frame,
                               text=f"✏️ Edit {person_data['name']}",
                               font=('Segoe UI', 16, 'bold'),
                               bg=COLORS['primary'],
                               fg=COLORS['white'])
        header_label.pack(pady=12)
        
        # Create main container with proper layout
        main_container = tk.Frame(edit_window, bg=COLORS['card'])
        main_container.pack(fill="both", expand=True, padx=30)
        
        # Scrollable form frame
        canvas = tk.Canvas(main_container, bg=COLORS['card'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview,
                                bg=COLORS['light'], width=12)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['card'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Form fields
        fields = {}
        
        # Name field (read-only for now)
        self.create_edit_field(scrollable_frame, "Name:", person_data['name'], fields, 'name', readonly=True)
        
        # Phone field
        self.create_edit_field(scrollable_frame, "Phone:", person_data.get('phone', ''), fields, 'phone')
        
        # Date of Birth field
        self.create_edit_field(scrollable_frame, "Date of Birth:", person_data.get('dob', ''), fields, 'dob')
        
        # Link field
        self.create_edit_field(scrollable_frame, "Link:", person_data.get('link', ''), fields, 'link')
        
        # Social Link field
        self.create_edit_field(scrollable_frame, "Social Link:", person_data.get('social_link', ''), fields, 'social_link')
        
        # Info field
        self.create_edit_field(scrollable_frame, "Info:", person_data.get('info', ''), fields, 'info', is_text=True)
        
        # Info1 field
        self.create_edit_field(scrollable_frame, "Info1:", person_data.get('info1', ''), fields, 'info1', is_text=True)
        
        # Note field
        self.create_edit_field(scrollable_frame, "Note:", person_data.get('note', ''), fields, 'note', is_text=True)
        
        # FIXED: Button frame - Always visible at bottom, not in scrollable area
        button_frame = tk.Frame(edit_window, bg=COLORS['card'])
        button_frame.pack(side="bottom", fill="x", padx=30, pady=(15, 25))
        
        # Cancel button
        cancel_btn = tk.Button(button_frame,
                              text="❌ Cancel",
                              command=edit_window.destroy,
                              bg=COLORS['text_light'],
                              fg=COLORS['white'],
                              font=('Segoe UI', 12, 'bold'),
                              relief='flat',
                              bd=0,
                              padx=25,
                              pady=10,
                              cursor='hand2',
                              width=12)
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # Save button
        save_btn = tk.Button(button_frame,
                            text="💾 Save Changes",
                            command=lambda: self.save_person_changes(person_data['id'], fields, edit_window),
                            bg=COLORS['success'],
                            fg=COLORS['white'],
                            font=('Segoe UI', 12, 'bold'),
                            relief='flat',
                            bd=0,
                            padx=25,
                            pady=10,
                            cursor='hand2',
                            width=15)
        save_btn.pack(side="right")
        
        # Hover effects
        self.add_button_hover_effect(cancel_btn, COLORS['text_light'], '#718096')
        self.add_button_hover_effect(save_btn, COLORS['success'], '#38A169')
        
        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def create_edit_field(self, parent, label_text, value, fields_dict, field_name, readonly=False, is_text=False):
        """Create an editable field in the form"""
        field_frame = tk.Frame(parent, bg=COLORS['card'])
        field_frame.pack(fill="x", pady=(0, 12))  # Reduced spacing between fields
        
        # Label
        label = tk.Label(field_frame,
                        text=label_text,
                        font=('Segoe UI', 11, 'bold'),  # Slightly larger font
                        bg=COLORS['card'],
                        fg=COLORS['text'])
        label.pack(anchor="w", pady=(0, 6))  # Reduced label padding
        
        # Entry or Text widget
        if is_text:
            widget = tk.Text(field_frame,
                           font=('Segoe UI', 10),
                           bg=COLORS['light'] if not readonly else COLORS['background'],
                           fg=COLORS['text'],
                           relief='flat',
                           bd=8,  # Increased border for better appearance
                           height=3,  # Reduced height for text fields from 4 to 3
                           wrap='word')
            widget.insert('1.0', value)
            if readonly:
                widget.configure(state='disabled')
        else:
            widget = tk.Entry(field_frame,
                            font=('Segoe UI', 11),  # Larger font
                            bg=COLORS['light'] if not readonly else COLORS['background'],
                            fg=COLORS['text'],
                            relief='flat',
                            bd=8,  # Increased border for better appearance
                            width=60)  # Wider entry fields
            widget.insert(0, value)
            if readonly:
                widget.configure(state='disabled')
        
        widget.pack(fill="x", ipady=6)  # Reduced internal padding from 8 to 6
        fields_dict[field_name] = widget
    
    def save_person_changes(self, person_id, fields, edit_window):
        """Save changes to the person"""
        try:
            # Get values from fields
            data = {}
            for field_name, widget in fields.items():
                if field_name == 'name':  # Skip name for now (read-only)
                    continue
                    
                if isinstance(widget, tk.Text):
                    data[field_name] = widget.get('1.0', 'end-1c')
                else:
                    data[field_name] = widget.get()
            
            # Update in database
            from db import update_person_details
            update_person_details(person_id, **data)
            
            # Refresh the UI
            self.refresh()
            
            # Close edit window
            edit_window.destroy()
            
            messagebox.showinfo("Success", "Person details updated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update person: {str(e)}")
    
    def get_person_data(self, name):
        """Get full person data by name"""
        try:
            from db import get_person_by_name
            return get_person_by_name(name)
        except Exception as e:
            print(f"Error getting person data: {e}")
            return None

    def delete_person(self):
        selection = self.people_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a person to delete.")
            return
            
        name = self.people_listbox.get(selection[0])
        if not messagebox.askyesno("Confirm Deletion", 
                                  f"Are you sure you want to delete '{name}' and all their data?\n\nThis action cannot be undone."):
            return
            
        person_data = get_person_by_name_legacy(self.con, name)
        if person_data:
            delete_person(self.con, person_data[0])
            self.refresh()
            
            # Hide details if this person was selected
            self.person_details_frame.pack_forget()
            self.no_selection_frame.pack(fill="both", expand=True)

class ModernLiveTab(ttk.Frame):
    def __init__(self, master, con):
        super().__init__(master)
        self.con = con
        self.worker = None
        self.imgtk = None
        self.detected_people = {}  # Track detected people
        self.src_var = tk.StringVar(value="0")  # Default camera source
        self.configure(style='Card.TFrame')
        self._build_modern_interface()

    def _build_modern_interface(self):
        # Main container
        main_frame = tk.Frame(self, bg=COLORS['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Top control panel
        self.create_control_panel(main_frame)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg=COLORS['background'])
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left - Video feed
        self.create_video_panel(content_frame)
        
        # Right - Detected people panel
        self.create_detected_panel(content_frame)

    def create_control_panel(self, parent):
        control_frame = tk.Frame(parent, bg=COLORS['card'], relief='solid', bd=1)
        control_frame.pack(fill="x", pady=(0, 8))
        
        inner_frame = tk.Frame(control_frame, bg=COLORS['card'])
        inner_frame.pack(fill="x", padx=15, pady=15)
        
        # Title
        title_label = tk.Label(inner_frame,
                              text="Live Face Recognition",
                              font=('Segoe UI', 16, 'bold'),
                              bg=COLORS['card'],
                              fg=COLORS['text'])
        title_label.pack(side="left")
        
        # Controls on the right
        controls_frame = tk.Frame(inner_frame, bg=COLORS['card'])
        controls_frame.pack(side="right")
        
        # Start and Stop buttons only
        start_btn = tk.Button(controls_frame,
                            text="▶️ Start",
                            command=self.start_video,
                            bg=COLORS['success'],
                            fg=COLORS['white'],
                            font=('Segoe UI', 10, 'bold'),
                            relief='flat',
                            padx=15,
                            pady=5)
        start_btn.pack(side="left", padx=(0, 5))
        
        stop_btn = tk.Button(controls_frame,
                           text="⏹️ Stop",
                           command=self.stop_video,
                           bg=COLORS['danger'],
                           fg=COLORS['white'],
                           font=('Segoe UI', 10, 'bold'),
                           relief='flat',
                           padx=15,
                           pady=5)
        stop_btn.pack(side="left")

    def create_video_panel(self, parent):
        video_frame = tk.Frame(parent, bg=COLORS['card'], relief='flat', bd=0)
        video_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        # Add subtle border effect
        border_frame = tk.Frame(video_frame, bg=COLORS['border'], height=1)
        border_frame.pack(fill="x", side="bottom")
        
        # Modern video header with gradient
        video_header = tk.Frame(video_frame, bg=COLORS['primary'], height=70)
        video_header.pack(fill="x")
        video_header.pack_propagate(False)
        
        header_content = tk.Frame(video_header, bg=COLORS['primary'])
        header_content.pack(expand=True, fill="both", padx=15)
        
        # Title on the left
        video_title = tk.Label(header_content,
                              text="📹 Live Video Feed",
                              font=('Segoe UI', 16, 'bold'),
                              bg=COLORS['primary'],
                              fg=COLORS['white'])
        video_title.pack(side="left", pady=15)
        
        # Stats on the right
        self.stats_var = tk.StringVar(value="Known: 0 | Unknown: 0 | Active Tracks: 0")
        stats_label = tk.Label(header_content,
                              textvariable=self.stats_var,
                              font=('Segoe UI', 10),
                              bg=COLORS['primary'],
                              fg=COLORS['light'])
        stats_label.pack(side="right", pady=15)
        
        # Video canvas with modern styling
        canvas_container = tk.Frame(video_frame, bg=COLORS['light'])
        canvas_container.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.canvas = tk.Label(canvas_container,
                              text="📹\n\nCamera Feed Display\n\nClick 'Start' to begin live recognition\n\nSupported: USB cameras, IP cameras",
                              font=('Segoe UI', 16),
                              bg=COLORS['light'],
                              fg=COLORS['text_light'],
                              justify='center')
        self.canvas.pack(fill="both", expand=True, padx=15, pady=15)

    def create_detected_panel(self, parent):
        detected_frame = tk.Frame(parent, bg=COLORS['card'], relief='flat', bd=0, width=380)
        detected_frame.pack(side="right", fill="y", padx=(15, 0))
        detected_frame.pack_propagate(False)
        
        # Add subtle border
        border_frame = tk.Frame(detected_frame, bg=COLORS['border'], width=1)
        border_frame.pack(fill="y", side="left")
        
        # Main content
        content_frame = tk.Frame(detected_frame, bg=COLORS['card'])
        content_frame.pack(fill="both", expand=True, padx=(2, 0))
        
        # Modern header with gradient effect
        header_frame = tk.Frame(content_frame, bg=COLORS['secondary'], height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=COLORS['secondary'])
        header_content.pack(expand=True, fill="both")
        
        header_label = tk.Label(header_content,
                               text="👥 Live Detections",
                               font=('Segoe UI', 16, 'bold'),
                               bg=COLORS['secondary'],
                               fg=COLORS['white'])
        header_label.pack(expand=True)
        
        # Scrollable frame for detected people with fixed mouse wheel
        canvas_container = tk.Frame(content_frame, bg=COLORS['card'])
        canvas_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Canvas with scrollbar
        self.detected_canvas = tk.Canvas(canvas_container, 
                                        bg=COLORS['card'], 
                                        highlightthickness=0,
                                        borderwidth=0)
        
        # Modern scrollbar
        scrollbar = tk.Scrollbar(canvas_container, 
                                orient="vertical", 
                                command=self.detected_canvas.yview,
                                bg=COLORS['light'],
                                troughcolor=COLORS['background'],
                                borderwidth=0,
                                highlightthickness=0,
                                width=12)
        
        self.detected_scrollable_frame = tk.Frame(self.detected_canvas, bg=COLORS['card'])
        
        # Configure scroll region
        def configure_scroll_region(event):
            self.detected_canvas.configure(scrollregion=self.detected_canvas.bbox("all"))
        
        self.detected_scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # Create canvas window
        self.canvas_window = self.detected_canvas.create_window((0, 0), 
                                                               window=self.detected_scrollable_frame, 
                                                               anchor="nw")
        
        # Configure canvas scrolling
        self.detected_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.detected_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel scrolling to the entire detected panel
        def _on_canvas_mousewheel(event):
            self.detected_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_canvas_mousewheel(event):
            self.detected_canvas.bind_all("<MouseWheel>", _on_canvas_mousewheel)
        
        def _unbind_canvas_mousewheel(event):
            self.detected_canvas.unbind_all("<MouseWheel>")
        
        # Bind to multiple widgets for better coverage
        for widget in [canvas_container, self.detected_canvas, self.detected_scrollable_frame]:
            widget.bind('<Enter>', _bind_canvas_mousewheel)
            widget.bind('<Leave>', _unbind_canvas_mousewheel)
        
        # Configure canvas window resizing
        def configure_canvas_window(event):
            canvas_width = event.width
            self.detected_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.detected_canvas.bind('<Configure>', configure_canvas_window)
        
        # Default message with modern styling
        self.no_detections_label = tk.Label(self.detected_scrollable_frame,
                                           text="👁️‍🗨️\n\nAwaiting Face Detection\n\nStart the camera to begin\nreal-time recognition",
                                           font=('Segoe UI', 14),
                                           bg=COLORS['card'],
                                           fg=COLORS['text_light'],
                                           justify='center')
        self.no_detections_label.pack(expand=True, pady=80)

    def detect_cameras(self):
        """Detect available cameras and update the UI"""
        logger.info("Detecting available cameras...")
        cameras = []
        
        # Check first 10 possible camera indices
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # Try to read a frame to confirm it's working
                    ret, frame = cap.read()
                    if ret:
                        cameras.append(i)
                        logger.info(f"Camera {i}: Available and working")
                    else:
                        logger.info(f"Camera {i}: Opens but cannot read frames")
                    cap.release()
                else:
                    logger.debug(f"Camera {i}: Not available")
            except Exception as e:
                logger.debug(f"Camera {i}: Error - {e}")
        
        if cameras:
            logger.info(f"Found {len(cameras)} working cameras: {cameras}")
            # Set default to first available camera
            self.src_var.set(str(cameras[0]))
        else:
            logger.warning("No working cameras found")
        
        return cameras

    def start_video(self):
        logger.info("Start video button clicked")
        if self.worker:
            logger.warning("VideoWorker already running, ignoring start request")
            return
        
        src_text = self.src_var.get().strip()
        logger.info(f"Video source input: '{src_text}'")
        
        try:
            src = int(src_text)
            logger.info(f"Parsed video source as camera index: {src}")
        except ValueError:
            src = src_text
            logger.info(f"Using video source as string: {src}")
        
        if isinstance(src, int):
            logger.info(f"Testing camera {src} availability...")
            test_cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
            if not test_cap.isOpened():
                error_msg = f"❌ Camera {src} not available"
                logger.error(error_msg)
                self.stats_var.set(error_msg)
                test_cap.release()
                return
            test_cap.release()
            logger.info(f"Camera {src} test successful")
        
        try:
            logger.info("Creating VideoWorker instance...")
            self.worker = VideoWorker(self.con, video_src=src, on_frame=self.on_frame, on_stats=self.on_stats)
            logger.info("Starting VideoWorker...")
            self.worker.start()
            logger.info("VideoWorker started successfully")
            self.stats_var.set("🔄 Starting camera...")
        except Exception as e:
            error_msg = f"❌ Failed to start video: {e}"
            logger.error(error_msg)
            self.stats_var.set(error_msg)
            self.worker = None

    def stop_video(self):
        if self.worker:
            self.worker.stop()
            self.worker = None
        
        # Reset canvas
        self.canvas.configure(image="",
                             text="📹\n\nCamera stopped\nClick 'Start' to begin",
                             font=('Segoe UI', 14),
                             bg=COLORS['light'],
                             fg=COLORS['text_light'])
        
        # Clear detected people
        self.clear_detected_people()

    def clear_detected_people(self):
        self.detected_people.clear()
        for widget in self.detected_scrollable_frame.winfo_children():
            widget.destroy()
        
        self.no_detections_label = tk.Label(self.detected_scrollable_frame,
                                           text="👁️\n\nNo people detected\nStart the camera to begin recognition",
                                           font=('Segoe UI', 12),
                                           bg=COLORS['card'],
                                           fg=COLORS['text_light'],
                                           justify='center')
        self.no_detections_label.pack(expand=True, pady=50)

    def on_frame(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        
        # Resize to fit display
        max_w, max_h = 640, 480
        if w > max_w or h > max_h:
            scale = min(max_w/w, max_h/h)
            new_w, new_h = int(w*scale), int(h*scale)
            rgb = cv2.resize(rgb, (new_w, new_h))
        
        img = Image.fromarray(rgb)
        self.imgtk = ImageTk.PhotoImage(img)
        self.canvas.configure(image=self.imgtk, text="")

    def on_stats(self, fps, known, unknown, tracks, detections):
        # Calculate active tracks as the sum of known and unknown
        active_tracks = known + unknown
        self.stats_var.set(f"Known: {known} | Unknown: {unknown} | Active Tracks: {active_tracks}")
        
        # Store track events in database using smart tracking
        from db import add_smart_track_event, get_person_by_name
        for detection in detections:
            track_id = detection.get('track_id')
            name = detection.get('name', 'Unknown')
            confidence = detection.get('confidence', 0.0)
            
            # Get person_id if known person
            person_id = None
            if name != 'Unknown':
                person_data = get_person_by_name(name)
                if person_data:
                    person_id = person_data['id']
            
            # Add smart track event (only if new session)
            kind = 'match' if name != 'Unknown' else 'unknown'
            event_added = add_smart_track_event(track_id, person_id, name, confidence, kind)
            
            if event_added:
                logger.info(f"New tracking session started: {name} ")
        
        # Update detected people panel
        self.update_detected_people(detections)

    def update_detected_people(self, detections):
        # Clear no detections message if it exists
        if hasattr(self, 'no_detections_label'):
            self.no_detections_label.destroy()
        
        # Update detected people
        current_tracks = set()
        
        for detection in detections:
            track_id = detection.get('track_id')
            name = detection.get('name', 'Unknown')
            confidence = detection.get('confidence', 0.0)
            
            current_tracks.add(track_id)
            
            if track_id not in self.detected_people:
                self.add_person_card(track_id, name, confidence)
            else:
                self.update_person_card(track_id, name, confidence)
        
        # Remove cards for tracks that are no longer active
        for track_id in list(self.detected_people.keys()):
            if track_id not in current_tracks:
                self.remove_person_card(track_id)

    def add_person_card(self, track_id, name, confidence):
        card_frame = tk.Frame(self.detected_scrollable_frame, bg=COLORS['white'], relief='solid', bd=1)
        card_frame.pack(fill="x", pady=5, padx=5)
        
        # Header
        header_frame = tk.Frame(card_frame, bg=COLORS['primary'] if name != 'Unknown' else COLORS['warning'])
        header_frame.pack(fill="x")
        
        name_label = tk.Label(header_frame,
                             text=name,
                             font=('Segoe UI', 10, 'bold'),  # Reduced from 12 to 10
                             bg=COLORS['primary'] if name != 'Unknown' else COLORS['warning'],
                             fg=COLORS['white'])
        name_label.pack(side="left", padx=10, pady=5)
        
        track_label = tk.Label(header_frame,
                              text=f" ",
                              font=('Segoe UI', 8),  # Reduced from 9 to 8
                              bg=COLORS['primary'] if name != 'Unknown' else COLORS['warning'],
                              fg=COLORS['light'])
        track_label.pack(side="right", padx=10, pady=5)
        
        # Body
        body_frame = tk.Frame(card_frame, bg=COLORS['white'])
        body_frame.pack(fill="x", padx=10, pady=8)
        
        if name != 'Unknown':
            conf_label = tk.Label(body_frame,
                                 text=f"Confidence: {confidence:.1%}",
                                 font=('Segoe UI', 9),  # Reduced from 10 to 9
                                 bg=COLORS['white'],
                                 fg=COLORS['text'])
            conf_label.pack(anchor="w")
            
            # Details button
            details_btn = tk.Button(body_frame,
                                  text="👤 View Details",
                                  command=lambda: self.show_person_details(name),
                                  bg=COLORS['info'],
                                  fg=COLORS['white'],
                                  font=('Segoe UI', 8, 'bold'),  # Reduced from 9 to 8
                                  relief='flat',
                                  padx=10,
                                  pady=3)
            details_btn.pack(anchor="w", pady=(5, 0))
        else:
            unknown_label = tk.Label(body_frame,
                                   text="Unrecognized person",
                                   font=('Segoe UI', 9),  # Reduced from 10 to 9
                                   bg=COLORS['white'],
                                   fg=COLORS['text_light'])
            unknown_label.pack(anchor="w")
        
        self.detected_people[track_id] = {
            'frame': card_frame,
            'name_label': name_label,
            'conf_label': conf_label if name != 'Unknown' else None
        }

    def update_person_card(self, track_id, name, confidence):
        if track_id in self.detected_people:
            card_data = self.detected_people[track_id]
            card_data['name_label'].config(text=name)
            if card_data['conf_label']:
                card_data['conf_label'].config(text=f"Confidence: {confidence:.1%}")

    def remove_person_card(self, track_id):
        if track_id in self.detected_people:
            self.detected_people[track_id]['frame'].destroy()
            del self.detected_people[track_id]

    def show_person_details(self, name):
        person_data = get_person_by_name_legacy(self.con, name)
        if person_data:
            PersonDetailsWindow(self, person_data)

    def refresh_gallery(self):
        if self.worker:
            self.worker.refresh_gallery()

class PersonDetailsWindow:
    def __init__(self, parent, person_data):
        self.window = tk.Toplevel(parent)
        self.window.title("Person Details")
        # Increased width and height for a bigger window
        self.window.geometry("1000x650")
        self.window.configure(bg=COLORS['background'])
        self.window.resizable(True, True)
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.window.winfo_screenheight() // 2) - (650 // 2)
        self.window.geometry(f"1000x650+{x}+{y}")
        self.build_details_view(person_data)


    def build_details_view(self, person_data):
        # Main container
        main_frame = tk.Frame(self.window, bg=COLORS['card'], relief='flat', bd=0)
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Extract data
        person_id, name, phone, dob, link, info, social_link, info1, note = person_data
        
        # Modern header with gradient
        header_frame = tk.Frame(main_frame, bg=COLORS['primary'], relief='flat', bd=0)
        header_frame.pack(fill="x", pady=(0, 25))
        
        header_content = tk.Frame(header_frame, bg=COLORS['primary'])
        header_content.pack(fill="x", padx=25, pady=20)
        
        name_label = tk.Label(header_content,
                             text=f"👤 {name}",
                             font=('Segoe UI', 20, 'bold'),
                             bg=COLORS['primary'],
                             fg=COLORS['white'])
        name_label.pack(anchor="w")
        
        id_frame = tk.Frame(header_content, bg=COLORS['info'])
        id_frame.pack(anchor="w", pady=(8, 0))
        
        id_label = tk.Label(id_frame,
                           text=f"ID: {person_id}",
                           font=('Segoe UI', 10, 'bold'),
                           bg=COLORS['info'],
                           fg=COLORS['white'])
        id_label.pack(padx=12, pady=4)
        
        # Scrollable content with fixed mouse wheel
        canvas_container = tk.Frame(main_frame, bg=COLORS['card'])
        canvas_container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_container, 
                          bg=COLORS['card'], 
                          highlightthickness=0,
                          borderwidth=0)
        
        scrollbar = tk.Scrollbar(canvas_container, 
                                orient="vertical", 
                                command=canvas.yview,
                                bg=COLORS['light'],
                                troughcolor=COLORS['background'],
                                borderwidth=0,
                                highlightthickness=0,
                                width=12)
        
        scrollable_frame = tk.Frame(canvas, bg=COLORS['card'])
        
        # Configure scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        # Bind to multiple widgets
        for widget in [canvas_container, canvas, scrollable_frame, main_frame]:
            widget.bind('<Enter>', _bind_mousewheel)
            widget.bind('<Leave>', _unbind_mousewheel)
        
        # Configure canvas window width
        def configure_canvas_window(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas.bind('<Configure>', configure_canvas_window)
        
        # Details with modern card design
        details = [
            ("📱 Phone Number", phone),
            ("🎂 Date of Birth", dob),
            ("🔗 Website/Link", link),
            ("📱 Social Media", social_link),
            ("ℹ️ General Information", info),
            ("📝 Additional Information", info1),
            ("📋 Notes", note)
        ]
        
        for icon_label, value in details:
            if value:  # Only show non-empty fields
                # Modern field card
                field_frame = tk.Frame(scrollable_frame, bg=COLORS['light'], relief='flat', bd=0)
                field_frame.pack(fill="x", pady=8, padx=10)
                
                # Field header
                header_bg = tk.Frame(field_frame, bg=COLORS['secondary'])
                header_bg.pack(fill="x")
                
                label = tk.Label(header_bg,
                               text=icon_label,
                               font=('Segoe UI', 12, 'bold'),
                               bg=COLORS['secondary'],
                               fg=COLORS['white'])
                label.pack(anchor="w", padx=15, pady=8)
                
                # Value container
                value_container = tk.Frame(field_frame, bg=COLORS['white'])
                value_container.pack(fill="x", padx=1, pady=(0, 1))
                
                # Value content
                if len(value) > 50:  # Long text
                    value_text = tk.Text(value_container,
                                       height=4,
                                       font=('Segoe UI', 11),
                                       bg=COLORS['white'],
                                       fg=COLORS['text'],
                                       relief='flat',
                                       wrap='word',
                                       borderwidth=0,
                                       highlightthickness=0,
                                       state='normal')
                    value_text.insert('1.0', value)
                    value_text.config(state='disabled')
                    value_text.pack(fill="x", padx=15, pady=15)
                else:  # Short text
                    value_label = tk.Label(value_container,
                                         text=value,
                                         font=('Segoe UI', 11),
                                         bg=COLORS['white'],
                                         fg=COLORS['text'],
                                         justify='left',
                                         wraplength=400)
                    value_label.pack(anchor="w", padx=15, pady=15)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Modern close button
        button_frame = tk.Frame(main_frame, bg=COLORS['card'])
        button_frame.pack(fill="x", pady=(25, 0))
        
        close_btn = tk.Button(button_frame,
                             text="✖️ Close Window",
                             command=self.window.destroy,
                             bg=COLORS['danger'],
                             fg=COLORS['white'],
                             font=('Segoe UI', 12, 'bold'),
                             relief='flat',
                             bd=0,
                             padx=25,
                             pady=12,
                             cursor='hand2')
        close_btn.pack(anchor="center")
        
        # Add hover effect to close button
        def on_close_hover(e):
            close_btn.config(bg='#C53030')
        
        def on_close_leave(e):
            close_btn.config(bg=COLORS['danger'])
        
        close_btn.bind("<Enter>", on_close_hover)
        close_btn.bind("<Leave>", on_close_leave)

class TrackHistoryTab(ttk.Frame):
    def __init__(self, master, con, root):
        super().__init__(master)
        self.con = con
        self.root = root
        self.configure(style='Card.TFrame')
        self._build_interface()

    def _build_interface(self):
        # Clean up any corrupted data first
        try:
            from db import clean_corrupted_events
            cleaned_count = clean_corrupted_events()
            if cleaned_count > 0:
                logger.info(f"Cleaned {cleaned_count} corrupted track history events")
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
        
        # Main container
        main_frame = tk.Frame(self, bg=COLORS['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with stats and controls
        self.create_header_panel(main_frame)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg=COLORS['background'])
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Track history list
        self.create_history_panel(content_frame)

    def create_header_panel(self, parent):
        header_frame = tk.Frame(parent, bg=COLORS['card'], relief='solid', bd=1)
        header_frame.pack(fill="x", pady=(0, 8))
        
        inner_frame = tk.Frame(header_frame, bg=COLORS['card'])
        inner_frame.pack(fill="x", padx=15, pady=15)
        
        # Title and stats on the left
        left_frame = tk.Frame(inner_frame, bg=COLORS['card'])
        left_frame.pack(side="left", fill="x", expand=True)
        
        title_label = tk.Label(left_frame,
                              text="📊 Track History",
                              font=('Segoe UI', 16, 'bold'),
                              bg=COLORS['card'],
                              fg=COLORS['text'])
        title_label.pack(anchor="w")
        
        # Stats display
        self.stats_frame = tk.Frame(left_frame, bg=COLORS['card'])
        self.stats_frame.pack(anchor="w", pady=(5, 0))
        
        self.stats_label = tk.Label(self.stats_frame,
                                   text="Loading statistics...",
                                   font=('Segoe UI', 10),
                                   bg=COLORS['card'],
                                   fg=COLORS['text_light'])
        self.stats_label.pack(anchor="w")
        
        # Controls on the right
        controls_frame = tk.Frame(inner_frame, bg=COLORS['card'])
        controls_frame.pack(side="right")
        
        # Refresh button
        refresh_btn = tk.Button(controls_frame,
                               text="🔄 Refresh",
                               command=self.refresh_history,
                               bg=COLORS['info'],
                               fg=COLORS['white'],
                               font=('Segoe UI', 10, 'bold'),
                               relief='flat',
                               padx=15,
                               pady=5)
        refresh_btn.pack(side="left", padx=(0, 5))
        
        # Clear history button
        clear_btn = tk.Button(controls_frame,
                             text="🗑️ Clear History",
                             command=self.clear_history,
                             bg=COLORS['danger'],
                             fg=COLORS['white'],
                             font=('Segoe UI', 10, 'bold'),
                             relief='flat',
                             padx=15,
                             pady=5)
        clear_btn.pack(side="left")

    def create_history_panel(self, parent):
        history_frame = tk.Frame(parent, bg=COLORS['card'], relief='flat', bd=0)
        history_frame.pack(fill="both", expand=True)
        
        # Add subtle border
        border_frame = tk.Frame(history_frame, bg=COLORS['border'], height=1)
        border_frame.pack(fill="x")
        
        # Header
        header_frame = tk.Frame(history_frame, bg=COLORS['primary'], height=50)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text="📋 Recent Track Events",
                               font=('Segoe UI', 14, 'bold'),
                               bg=COLORS['primary'],
                               fg=COLORS['white'])
        header_label.pack(expand=True)
        
        # Scrollable history list
        list_container = tk.Frame(history_frame, bg=COLORS['card'])
        list_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Canvas with scrollbar for history items
        self.history_canvas = tk.Canvas(list_container,
                                       bg=COLORS['card'],
                                       highlightthickness=0,
                                       borderwidth=0)
        
        scrollbar = tk.Scrollbar(list_container,
                                orient="vertical",
                                command=self.history_canvas.yview,
                                bg=COLORS['light'],
                                troughcolor=COLORS['background'],
                                borderwidth=0,
                                highlightthickness=0,
                                width=12)
        
        self.history_scrollable_frame = tk.Frame(self.history_canvas, bg=COLORS['card'])
        
        # Configure scroll region
        def configure_scroll_region(event):
            self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        
        self.history_scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # Create canvas window
        self.canvas_window = self.history_canvas.create_window((0, 0),
                                                              window=self.history_scrollable_frame,
                                                              anchor="nw")
        
        # Configure canvas scrolling
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            self.history_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            self.history_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            self.history_canvas.unbind_all("<MouseWheel>")
        
        self.history_canvas.bind('<Enter>', _bind_mousewheel)
        self.history_canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Configure canvas window width
        def configure_canvas_window(event):
            canvas_width = event.width
            self.history_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.history_canvas.bind('<Configure>', configure_canvas_window)
        
        # Load initial data
        self.refresh_history()

    def refresh_history(self):
        """Refresh the track history display"""
        # Clear existing items
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get track history and stats
        from db import get_track_history, get_track_stats
        
        try:
            # Update stats with enhanced information
            stats = get_track_stats()
            
            # Create more informative stats display
            total_entries = stats['total_events']
            unique_people = stats['unique_people']
            today_activity = stats.get('today_activity', 0)
            
            stats_text = f"Total Entries: {total_entries} | Unique People: {unique_people} | Today's Activity: {today_activity}"
            self.stats_label.config(text=stats_text)
            
            # Get history events
            history = get_track_history(100)  # Get last 100 events
            
            if not history:
                # No history message
                no_history_label = tk.Label(self.history_scrollable_frame,
                                           text="📝\n\nNo track history available\n\nStart live recognition to generate entry events\n\n💡 Note: Only new entries are recorded,\nnot continuous detections",
                                           font=('Segoe UI', 14),
                                           bg=COLORS['card'],
                                           fg=COLORS['text_light'],
                                           justify='center')
                no_history_label.pack(expand=True, pady=50)
            else:
                # Add summary info at the top
                if stats.get('frequent_visitors'):
                    summary_frame = tk.Frame(self.history_scrollable_frame, bg=COLORS['light'], relief='solid', bd=1)
                    summary_frame.pack(fill="x", pady=(0, 10), padx=5)
                    
                    summary_header = tk.Label(summary_frame,
                                            text="📊 Most Frequent Visitors Today",
                                            font=('Segoe UI', 11, 'bold'),
                                            bg=COLORS['light'],
                                            fg=COLORS['text'])
                    summary_header.pack(pady=5)
                    
                    for name, visits in stats['frequent_visitors'][:3]:  # Top 3
                        visitor_label = tk.Label(summary_frame,
                                               text=f"• {name}: {visits} entries",
                                               font=('Segoe UI', 9),
                                               bg=COLORS['light'],
                                               fg=COLORS['text'])
                        visitor_label.pack()
                    
                    # Spacer
                    spacer = tk.Frame(self.history_scrollable_frame, bg=COLORS['card'], height=10)
                    spacer.pack(fill="x")
                
                # Display history events
                for event in history:
                    self.create_history_item(event)
                    
        except Exception as e:
            # Error message
            error_label = tk.Label(self.history_scrollable_frame,
                                  text=f"❌\n\nError loading track history:\n{str(e)}",
                                  font=('Segoe UI', 12),
                                  bg=COLORS['card'],
                                  fg=COLORS['danger'],
                                  justify='center')
            error_label.pack(expand=True, pady=50)

    def create_history_item(self, event):
        """Create a history item card"""
        # Ensure all event data is properly typed with robust error handling
        try:
            # Convert bytes to strings if needed, with multiple fallback strategies
            for key, value in event.items():
                if isinstance(value, bytes):
                    try:
                        # Try UTF-8 first
                        event[key] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            # Try latin-1 as fallback (can decode any byte sequence)
                            event[key] = value.decode('latin-1')
                            logger.warning(f"Used latin-1 fallback for {key}")
                        except UnicodeDecodeError:
                            # Last resort: ignore errors and use replacement characters
                            event[key] = value.decode('utf-8', errors='replace')
                            logger.warning(f"Used replacement characters for corrupted {key}")
                        
                        # Apply safe defaults for specific fields
                        if key == 'name' and not event[key].isprintable():
                            event[key] = 'Unknown'
                        elif key == 'timestamp' and not event[key].isprintable():
                            event[key] = '1970-01-01 00:00:00'
                            
        except Exception as e:
            logger.error(f"Error processing event data: {e}")
            # If all else fails, create a minimal safe event
            event = {
                'id': event.get('id', 0),
                'timestamp': '1970-01-01 00:00:00',
                'track_id': event.get('track_id', 0),
                'name': 'Unknown',
                'confidence': 0.0,
                'kind': 'unknown'
            }
        
        # Main card frame
        card_frame = tk.Frame(self.history_scrollable_frame,
                             bg=COLORS['white'],
                             relief='solid',
                             bd=1)
        card_frame.pack(fill="x", pady=3, padx=5)
        
        # Event kind determines color and display
        kind = event.get('kind', 'unknown')
        if kind == 'match':
            bg_color = COLORS['success']
            icon = "✅"
            display_text = "Person Recognized"
        elif kind == 'enter':
            bg_color = COLORS['primary'] 
            icon = "🚪"
            display_text = "Person Entered"
        elif kind == 'unknown':
            bg_color = COLORS['warning'] 
            icon = "❓"
            display_text = "Unknown Person"
        else:
            bg_color = COLORS['info']
            icon = "ℹ️"
            display_text = kind.title()
        
        # Header with event type
        header_frame = tk.Frame(card_frame, bg=bg_color)
        header_frame.pack(fill="x")
        
        # Left side - icon and type
        left_header = tk.Frame(header_frame, bg=bg_color)
        left_header.pack(side="left", fill="x", expand=True)
        
        type_label = tk.Label(left_header,
                             text=f"{icon} {display_text}",
                             font=('Segoe UI', 10, 'bold'),
                             bg=bg_color,
                             fg=COLORS['white'])
        type_label.pack(side="left", padx=10, pady=5)
        
        # Right side - timestamp
        timestamp = event.get('timestamp', '')
        # Robust timestamp formatting
        formatted_time = 'N/A'
        formatted_date = ''
        
        try:
            # Handle different timestamp formats
            if isinstance(timestamp, bytes):
                timestamp = timestamp.decode('utf-8')
            
            if timestamp:
                from datetime import datetime
                # Try different timestamp formats
                try:
                    # SQLite default format: YYYY-MM-DD HH:MM:SS
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        # ISO format with microseconds
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        # Just use the timestamp as-is
                        formatted_time = str(timestamp)
                        dt = None
                
                if dt:
                    formatted_time = dt.strftime('%H:%M:%S')
                    formatted_date = dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"Error formatting timestamp '{timestamp}': {e}")
            formatted_time = str(timestamp) if timestamp else 'N/A'
        
        time_label = tk.Label(header_frame,
                             text=f"{formatted_date} {formatted_time}",
                             font=('Segoe UI', 9),
                             bg=bg_color,
                             fg=COLORS['light'])
        time_label.pack(side="right", padx=10, pady=5)
        
        # Body with enhanced details
        body_frame = tk.Frame(card_frame, bg=COLORS['white'])
        body_frame.pack(fill="x", padx=10, pady=8)
        
        # Track ID and Name with better formatting
        track_id = event.get('track_id', 'N/A')
        name = event.get('name', 'Unknown')
        confidence = event.get('confidence', 0.0)
        kind = event.get('kind', 'unknown')
        
        # Create more descriptive text based on event type
        if kind == 'enter':
            if name != 'Unknown':
                details_text = f"👤 {name} entered the area"
            else:
                details_text = f"👤 Unknown person entered (Track #{track_id})"
        elif kind == 'match':
            details_text = f"👤 {name} recognized in area"
        else:
            details_text = f"👤 {name} detected"
        
        if confidence > 0:
            details_text += f" • Confidence: {confidence:.1%}"
        
        # Main details
        details_label = tk.Label(body_frame,
                                text=details_text,
                                font=('Segoe UI', 10, 'bold'),
                                bg=COLORS['white'],
                                fg=COLORS['text'])
        details_label.pack(anchor="w")
        
        # Additional info line
        if track_id and track_id != 'N/A':
            info_text = f" "
            info_label = tk.Label(body_frame,
                                 text=info_text,
                                 font=('Segoe UI', 9),
                                 bg=COLORS['white'],
                                 fg=COLORS['text_light'])
            info_label.pack(anchor="w", pady=(2, 0))

    def clear_history(self):
        """Clear all track history"""
        result = messagebox.askyesno("Confirm Clear History",
                                   "Are you sure you want to clear all track history?\n\nThis action cannot be undone.")
        if result:
            try:
                from db import clear_track_history
                deleted_count = clear_track_history()
                messagebox.showinfo("Success", f"Cleared {deleted_count} track history events!")
                self.refresh_history()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear track history: {str(e)}")

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("FaceScannerPro Application Starting")
    logger.info("="*50)
    
    try:
        app = App()
        logger.info("Starting main application loop")
        app.mainloop()
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("FaceScannerPro Application Exiting")
