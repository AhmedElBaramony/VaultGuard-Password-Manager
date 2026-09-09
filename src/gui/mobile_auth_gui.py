import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import requests
import pyotp
import time
import urllib3
import json
import os

# Suppress warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MobileAuthGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VaultGuard Authenticator")
        self.root.geometry("400x700")
        self.root.resizable(False, False)
        
        self.server_url = "https://127.0.0.1:5000"
        self.username = None
        self.secret = None
        self.otp_label = None
        self.timer_label = None
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.saved_users_file = os.path.join(base_dir, 'data', 'mobile_users.json')
        
        # Load data
        self.saved_users = self.load_saved_users()
        
        # Main Layout
        self.main_container = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_login_screen()
        
    def load_saved_users(self):
        if os.path.exists(self.saved_users_file):
            try:
                with open(self.saved_users_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_users(self):
        with open(self.saved_users_file, 'w') as f:
            json.dump(self.saved_users, f, indent=4)
            
    def clear_view(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_view()
        
        # Logo Area
        ctk.CTkLabel(self.main_container, text="🛡️", font=("Arial", 64)).pack(pady=(40, 10))
        ctk.CTkLabel(self.main_container, text="VaultGuard", font=("Roboto Medium", 24)).pack()
        ctk.CTkLabel(self.main_container, text="Authenticator", font=("Roboto", 16), text_color="gray").pack(pady=(0, 30))
        
        # Saved Users List
        if self.saved_users:
            ctk.CTkLabel(self.main_container, text="Select Account", font=("Roboto Medium", 14), anchor="w").pack(fill="x", pady=5)
            
            scroll_users = ctk.CTkScrollableFrame(self.main_container, height=200, label_text="Registered Accounts")
            scroll_users.pack(fill="x", pady=(0, 20))
            
            for username in self.saved_users:
                btn = ctk.CTkButton(scroll_users, text=f"👤  {username}", 
                                  command=lambda u=username: self.login_user(u),
                                  height=40, font=("Roboto", 14), anchor="w", fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
                btn.pack(fill="x", pady=2)
                
        # Actions
        ctk.CTkButton(self.main_container, text="Scan / Register New Device", 
                      command=self.show_register_screen, height=50, font=("Roboto Medium", 14)).pack(side="bottom", pady=10, fill="x")

    def show_register_screen(self):
        self.clear_view()
        
        ctk.CTkLabel(self.main_container, text="Add Account", font=("Roboto Medium", 24)).pack(pady=(20, 40))
        
        self.reg_username_entry = ctk.CTkEntry(self.main_container, placeholder_text="Username", height=50)
        self.reg_username_entry.pack(fill="x", pady=20)
        
        ctk.CTkButton(self.main_container, text="Connect & Register", command=self.register, height=50, fg_color="#2ecc71", hover_color="#27ae60").pack(fill="x", pady=10)
        
        ctk.CTkButton(self.main_container, text="Back", command=self.show_login_screen, fg_color="transparent", text_color="gray").pack(pady=10)

    def register(self):
        username = self.reg_username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Username cannot be empty")
            return
            
        try:
            response = requests.post(f"{self.server_url}/register", json={"username": username}, verify=False, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.secret = data['secret']
                self.username = username
                self.saved_users[username] = self.secret
                self.save_users()
                
                messagebox.showinfo("Success", f"Device registered for '{username}'!")
                self.show_otp_screen()
            elif response.status_code == 409:
                messagebox.showerror("Conflict", "This username is already registered.")
            else:
                messagebox.showerror("Error", f"Server error: {response.text}")
                
        except Exception as e:
            messagebox.showerror("Network Error", f"Could not connect to MFA Server:\n{str(e)}")

    def login_user(self, username):
        self.username = username
        self.secret = self.saved_users[username]
        self.show_otp_screen()

    def show_otp_screen(self):
        self.clear_view()
        
        # Top Bar
        top_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkButton(top_frame, text="🔒 Lock", width=60, command=self.logout, fg_color="transparent", border_width=1).pack(side="right")
        ctk.CTkLabel(top_frame, text=self.username, font=("Roboto Medium", 16)).pack(side="left", padx=5)

        # OTP Circle/Display
        otp_card = ctk.CTkFrame(self.main_container, corner_radius=20, fg_color=("gray85", "gray20"))
        otp_card.pack(fill="x", pady=20, ipady=30)
        
        ctk.CTkLabel(otp_card, text="One-Time Password", text_color="gray").pack(pady=(20, 5))
        
        self.otp_label = ctk.CTkLabel(otp_card, text="--- ---", font=("Courier New", 45, "bold"), text_color="#3498db")
        self.otp_label.pack(pady=10)
        
        self.timer_label = ctk.CTkLabel(otp_card, text="60s", font=("Roboto Medium", 16), text_color="#e74c3c")
        self.timer_label.pack(pady=5)
        
        # Copy Button
        ctk.CTkButton(self.main_container, text="Tap to Copy Code", command=self.copy_otp, height=50, font=("Roboto Medium", 14)).pack(fill="x", pady=20)
        
        # Delete Button
        ctk.CTkButton(self.main_container, text="Remove Account", command=self.delete_user, fg_color="transparent", text_color="#e74c3c", hover_color="#fadbd8").pack(side="bottom", pady=10)

        self.update_otp()

    def update_otp(self):
        if not self.secret or not self.main_container.winfo_exists():
            return
            
        try:
            totp = pyotp.TOTP(self.secret, interval=60)
            otp_code = totp.now()
            # Format as 123 456
            formatted_otp = f"{otp_code[:3]} {otp_code[3:]}"
            
            remaining = int(totp.interval - (time.time() % totp.interval))
            
            if self.otp_label and self.otp_label.winfo_exists():
                self.otp_label.configure(text=formatted_otp)
                self.timer_label.configure(text=f"Expires in {remaining}s")
                
                # Color code timer
                if remaining < 10:
                    self.timer_label.configure(text_color="#e74c3c") # Red
                else:
                     self.timer_label.configure(text_color="#2ecc71") # Green
            
            self.root.after(1000, self.update_otp)
            
        except Exception:
            pass

    def copy_otp(self):
        if self.secret:
            totp = pyotp.TOTP(self.secret, interval=60)
            self.root.clipboard_clear()
            self.root.clipboard_append(totp.now())
            
            # Flash effect (optional)
            original_text = self.otp_label.cget("text_color")
            self.otp_label.configure(text_color="white")
            self.root.after(200, lambda: self.otp_label.configure(text_color=original_text))

    def logout(self):
        self.secret = None
        self.username = None
        self.show_login_screen()

    def delete_user(self):
        if messagebox.askyesno("Remove Account", f"Remove {self.username} from this device?"):
            del self.saved_users[self.username]
            self.save_users()
            self.logout()

if __name__ == "__main__":
    root = ctk.CTk()
    app = MobileAuthGUI(root)
    root.mainloop()