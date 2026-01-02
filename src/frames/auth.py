import customtkinter as ctk

class SetupFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.label = ctk.CTkLabel(self, text="Create PIN", font=("Roboto", 24))
        self.label.pack(pady=40)
        
        self.pin_entry = ctk.CTkEntry(self, placeholder_text="Enter new 4-digit PIN", show="*")
        self.pin_entry.pack(pady=10)
        
        self.confirm_entry = ctk.CTkEntry(self, placeholder_text="Confirm PIN", show="*")
        self.confirm_entry.pack(pady=10)
        
        self.btn = ctk.CTkButton(self, text="Set PIN", command=self.submit)
        self.btn.pack(pady=20)
        
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack()

    def submit(self):
        p1 = self.pin_entry.get()
        p2 = self.confirm_entry.get()
        
        if len(p1) < 4:
            self.error_label.configure(text="PIN must be at least 4 digits")
            return
        if p1 != p2:
            self.error_label.configure(text="PINs do not match")
            return
            
        self.controller.on_setup(p1)


class LockFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.label = ctk.CTkLabel(self, text="Locked", font=("Roboto", 24))
        self.label.pack(pady=40)
        
        self.pin_entry = ctk.CTkEntry(self, placeholder_text="Enter PIN to Unlock", show="*")
        self.pin_entry.pack(pady=10)
        
        self.btn = ctk.CTkButton(self, text="Unlock", command=self.submit)
        self.btn.pack(pady=20)
        
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack()

    def submit(self):
        pin = self.pin_entry.get()
        if not self.controller.on_unlock(pin):
            self.error_label.configure(text="Invalid PIN")
