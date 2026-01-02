import os
import sys
from PIL import Image, ImageTk
import customtkinter as ctk
from .storage import StorageManager
from .erp_client import ERPClient
from .frames.auth import SetupFrame, LockFrame
from .frames.main_view import MainViewFrame
import threading
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class ERPApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("IIT KGP ERP Manager")
        self.geometry("800x600")
        
        # Set Icon
        try:
            icon_path = resource_path(os.path.join("assets", "logo.png"))
            if os.path.exists(icon_path):
                # Use PIL to load the image
                img = Image.open(icon_path)
                icon = ImageTk.PhotoImage(img)
                self.wm_iconphoto(True, icon)
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")

        # Logic Components
        self.storage = StorageManager()
        self.client = ERPClient()
        self.is_auto_login_active = False

        # Container
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        self.current_frame = None

        self.init_app_state()

    def init_app_state(self):
        # Check vault
        if not self.storage.exists():
            self.show_frame("SetupFrame")
        else:
            self.show_frame("LockFrame")

    def show_frame(self, frame_name, **kwargs):
        if self.current_frame:
            self.current_frame.pack_forget()
            # If not caching frames, destroy them? maybe better to destroy to reset state
            self.current_frame.destroy()
            self.frames.pop(frame_name, None) 

        if frame_name == "SetupFrame":
            frame = SetupFrame(self.container, self)
        elif frame_name == "LockFrame":
            frame = LockFrame(self.container, self)
        elif frame_name == "MainViewFrame":
            frame = MainViewFrame(self.container, self)
        else:
            return

        self.frames[frame_name] = frame
        self.current_frame = frame
        frame.pack(fill="both", expand=True)

    def on_unlock(self, pin):
         # Try to unlock
         if self.storage.unlock(pin):
             self.pin = pin # Keep in memory for re-saving
             self.show_frame("MainViewFrame")
             self.start_auto_login_service()
             return True
         return False

    def on_setup(self, pin):
        # Create vault
        self.storage.init_vault(pin)
        self.pin = pin
        self.show_frame("MainViewFrame")

    def start_auto_login_service(self):
        if self.is_auto_login_active: return
        self.is_auto_login_active = True
        
        thread = threading.Thread(target=self._auto_login_loop, daemon=True)
        thread.start()
        
    def _auto_login_loop(self):
        print("Auto-login service started")
        while True:
            try:
                if not self.client.is_session_alive():
                    creds = self.storage.get_credentials()
                    if creds and creds.get('roll_number'):
                        print("Session dead. Attempting auto-login...")
                        # We need to run this carefully, maybe update status in UI?
                        # Since this is a thread, update via callback?
                        try:
                            self.client.login_with_credentials(creds)
                            print("Auto-login successful")
                        except Exception as e:
                            print(f"Auto-login failed: {e}")
                else:
                    # Session alive
                    pass
            except Exception as e:
                print(f"Auto-login loop error: {e}")
            
            time.sleep(60) # Check every minute

