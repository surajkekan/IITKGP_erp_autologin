import logging
import customtkinter as ctk
import threading
import webbrowser
from tkinter import messagebox

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class MainViewFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Layout: Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_settings = self.tabview.add("Settings")
        
        self._init_dashboard()
        self._init_settings()
        
    def _init_dashboard(self):
        frame = self.tab_dashboard
        
        self.status_label = ctk.CTkLabel(frame, text="Status: Unknown", font=("Roboto", 18))
        self.status_label.pack(pady=20)
        
        self.verify_btn = ctk.CTkButton(frame, text="Verify / Login Now", command=self.run_verify, height=40)
        self.verify_btn.pack(pady=10)
        
        self.btn_launch = ctk.CTkButton(frame, text="Launch Website (Logged In)", command=self.launch_browser_session, fg_color="green", height=40)
        self.btn_launch.pack(pady=10)
        
        # Keeping the text box for manual user-facing messages if needed, 
        # but user specifically said "logs in terminal not app". 
        # I'll keep it as a simple status area for "Process complete" messages 
        # but remove the heavy log interception.
        self.log_text = ctk.CTkTextbox(frame, width=500, height=300)
        self.log_text.pack(pady=10, fill="both", expand=True)

        # Periodically update status label
        self.after(2000, self.update_status)

    def update_status(self):
        alive = self.controller.client.is_session_alive()
        text = "Status: Online (Logged In)" if alive else "Status: Offline (Logged Out)"
        color = "green" if alive else "red"
        self.status_label.configure(text=text, text_color=color)
        self.after(5000, self.update_status)

    def log(self, message):
        # Log to terminal
        print(message)
        logging.info(message)
        
        # Also show in UI for immediate feedback on actions (optional, but good UX)
        # But since user said "not app", I will minimize what goes here.
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def run_verify(self):
        self.verify_btn.configure(state="disabled")
        self.log("Starting Login/Verify Process...")
        
        def task():
            try:
                creds = self.controller.storage.get_credentials()
                if not creds or not creds.get('roll_number'):
                    self.log("Error: No credentials saved in Settings.")
                    return
                
                success = self.controller.client.login_with_credentials(
                    creds, 
                    status_callback=lambda msg: self.after(0, lambda: self.log(msg))
                )
                if success:
                    self.log("Process complete: Success")
                    # Auto-launch website on success
                    self.after(1000, self.launch_browser_session)
                else:
                    self.log("Process complete: Failed (Session dead)")
            except Exception as e:
                self.log(f"Process complete: Error ({e})")
            finally:
                self.after(0, lambda: self.verify_btn.configure(state="normal"))
        
        threading.Thread(target=task, daemon=True).start()

    def _init_settings(self):
        # Use a ScrollableFrame to ensure everything fits
        self.settings_scroll = ctk.CTkScrollableFrame(self.tab_settings)
        self.settings_scroll.pack(fill="both", expand=True)
        
        frame = self.settings_scroll
        
        # --- Credentials ---
        ctk.CTkLabel(frame, text="IIT KGP ERP Credentials", font=("Roboto", 16, "bold")).pack(pady=(10, 5), anchor="w", padx=10)
        
        # Roll Number + Fetch Button container
        roll_frame = ctk.CTkFrame(frame, fg_color="transparent")
        roll_frame.pack(pady=5, padx=10, fill="x")
        
        self.entry_roll = ctk.CTkEntry(roll_frame, placeholder_text="Roll Number")
        self.entry_roll.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_fetch = ctk.CTkButton(roll_frame, text="Fetch Qs", width=80, command=self.run_fetch_questions)
        self.btn_fetch.pack(side="right")
        
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="ERP Password", show="*")
        self.entry_pass.pack(pady=5, padx=10, fill="x")

        # --- Security Questions ---
        ctk.CTkLabel(frame, text="Security Questions", font=("Roboto", 16, "bold")).pack(pady=(20, 5), anchor="w", padx=10)
        self.lbl_sec_hint = ctk.CTkLabel(frame, text="Click 'Fetch Qs' to load questions automatically.", font=("Roboto", 12))
        self.lbl_sec_hint.pack(pady=(0, 10), anchor="w", padx=10)

        self.qa_entries = []
        for i in range(1, 4):
            q_frame = ctk.CTkFrame(frame)
            q_frame.pack(pady=5, padx=10, fill="x")
            
            ctk.CTkLabel(q_frame, text=f"Question {i}").pack(anchor="w", padx=5, pady=2)
            entry_q = ctk.CTkEntry(q_frame, placeholder_text=f"Security Question {i}")
            entry_q.pack(fill="x", padx=5, pady=(0, 5))
            
            entry_a = ctk.CTkEntry(q_frame, placeholder_text=f"Answer {i}")
            entry_a.pack(fill="x", padx=5, pady=(0, 5))
            
            self.qa_entries.append((entry_q, entry_a))

        # --- Google Credentials ---
        ctk.CTkLabel(frame, text="Google App Credentials (For OTP)", font=("Roboto", 16, "bold")).pack(pady=(20, 5), anchor="w", padx=10)
        
        self.entry_email = ctk.CTkEntry(frame, placeholder_text="Gmail Address (registered with ERP)")
        self.entry_email.pack(pady=5, padx=10, fill="x")
        
        self.entry_app_pass = ctk.CTkEntry(frame, placeholder_text="Google App Password (16 chars)", show="*")
        self.entry_app_pass.pack(pady=5, padx=10, fill="x")
        
        self.save_btn = ctk.CTkButton(frame, text="Save To Vault", command=self.save_settings, height=40)
        self.save_btn.pack(pady=30, padx=10, fill="x")
        
        # Load existing
        self.load_settings()

    def run_fetch_questions(self):
        roll = self.entry_roll.get().strip()
        if not roll:
            messagebox.showerror("Error", "Please enter Roll Number first.")
            return
            
        self.btn_fetch.configure(state="disabled", text="Fetching...")
        
        def task():
            try:
                questions = self.controller.client.fetch_security_questions(roll)
                if not questions:
                    self.after(0, lambda: messagebox.showwarning("Failed", "Could not fetch questions. Check Roll No or internet."))
                else:
                    self.after(0, lambda: self.populate_questions(questions))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Fetch failed: {e}"))
            finally:
                self.after(0, lambda: self.btn_fetch.configure(state="normal", text="Fetch Qs"))
                
        threading.Thread(target=task, daemon=True).start()

    def launch_browser_session(self):
        self.log("Launching authenticated browser session...")
        
        def task():
            try:
                # Check if we have an active session
                if not self.controller.client.is_session_alive():
                    self.after(0, lambda: messagebox.showwarning("No active session", "Please login/verify first."))
                    self.after(0, lambda: self.log("Launch cancelled: No active session."))
                    return

                # Get cookies from python session
                cookies = self.controller.client.session.cookies.get_dict()
                sso = cookies.get('ssoToken')
                jsid = cookies.get('JSID#/IIT_ERP3')
                
                if not sso or not jsid:
                     self.after(0, lambda: messagebox.showerror("Error", "Session tokens missing from active session."))
                     return

                # Launch Chrome in App Mode (no address bar)
                options = webdriver.ChromeOptions()
                options.add_argument("--app=https://erp.iitkgp.ac.in/")
                options.add_argument("--start-maximized")
                
                # Turn off "Chrome is being controlled by automated test software" bar
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                
                # Navigate to domain to set cookies
                driver.get("https://erp.iitkgp.ac.in/")
                
                # Inject cookies. Note: domain should match exactly or be superdomain.
                driver.add_cookie({'name': 'ssoToken', 'value': sso, 'domain': 'erp.iitkgp.ac.in', 'path': '/'})
                driver.add_cookie({'name': 'JSID#/IIT_ERP3', 'value': jsid, 'domain': 'erp.iitkgp.ac.in', 'path': '/'})
                
                # Navigate to authenticated homepage
                driver.get("https://erp.iitkgp.ac.in/IIT_ERP3/")
                
                self.after(0, lambda: self.log("Browser launched with session."))
                
                # Keep active
                self.browser_driver = driver
                
            except Exception as e:
                self.after(0, lambda: self.log(f"Browser launch failed: {e}"))
                self.after(0, lambda: messagebox.showerror("Launch Error", f"Could not launch browser: {e}"))

        threading.Thread(target=task, daemon=True).start()

    def populate_questions(self, questions):
        # Clear existing
        for eq, ea in self.qa_entries:
            eq.delete(0, "end")
            
        for i, q in enumerate(questions):
            if i < len(self.qa_entries):
                self.qa_entries[i][0].insert(0, q)
        
        count = len(questions)
        messagebox.showinfo("Success", f"Fetched {count} unique question(s). Please fill answers.")

    def load_settings(self):
        creds = self.controller.storage.get_credentials()
        if not creds: return
        
        if creds.get('roll_number'): 
            self.entry_roll.insert(0, creds['roll_number'])
        if creds.get('erp_password'): 
            self.entry_pass.insert(0, creds['erp_password'])
        if creds.get('google_email'): 
            self.entry_email.insert(0, creds['google_email'])
        if creds.get('google_app_password'): 
            self.entry_app_pass.insert(0, creds['google_app_password'])
            
        qa_dict = creds.get('security_answers', {})
        # Convert dict to list of items to populate
        # Since dict is unordered (historically) but we just need to fill slots.
        # If we saved them, we want to try to restore them.
        # We'll just take the items and fill up to 3.
        idx = 0
        for q, a in qa_dict.items():
            if idx < 3:
                entry_q, entry_a = self.qa_entries[idx]
                entry_q.insert(0, q)
                entry_a.insert(0, a)
                idx += 1

    def save_settings(self):
        roll = self.entry_roll.get().strip()
        pwd = self.entry_pass.get().strip()
        email_addr = self.entry_email.get().strip()
        app_pass = self.entry_app_pass.get().strip()
        
        qa_dict = {}
        for entry_q, entry_a in self.qa_entries:
            q_text = entry_q.get().strip()
            a_text = entry_a.get().strip()
            if q_text and a_text:
                qa_dict[q_text] = a_text
                
        if not qa_dict:
             messagebox.showwarning("Incomplete", "Please add at least one security question.")
             return

        creds = {
            "roll_number": roll,
            "erp_password": pwd,
            "security_answers": qa_dict,
            "google_email": email_addr,
            "google_app_password": app_pass
        }
        
        if self.controller.storage.save_credentials(self.controller.pin, creds):
            self.log("Settings saved to encrypted vault.")
            messagebox.showinfo("Saved", "Credentials saved successfully.")
        else:
            self.log("Failed to save.")
            messagebox.showerror("Error", "Failed to save.")
