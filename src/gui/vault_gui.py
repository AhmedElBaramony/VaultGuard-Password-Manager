import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
import sys

# Add project root to sys.path to ensure module resolution works
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.vault_file_manager import VaultFileManager
from src.core.crypto_manager import CryptoManager
from src.auth.mfa_client import MFAService

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VaultGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VaultGuard  |  Secure Password Manager")
        self.root.geometry("900x700")
        
        # Initialize Core Systems
        self.file_manager = VaultFileManager()
        self.crypto = CryptoManager()
        self.mfa = MFAService()
        self.credentials = []
        self.master_password = None
        
        # Configure Grid Layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.show_login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_window()
        
        # Main Container
        login_frame = ctk.CTkFrame(self.root, corner_radius=15, width=400)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Header
        ctk.CTkLabel(login_frame, text="🔒 VaultGuard", font=("Roboto Medium", 28)).pack(pady=(40, 10), padx=50)
        ctk.CTkLabel(login_frame, text="Enterprise-Grade Security", font=("Roboto", 12), text_color="gray").pack(pady=(0, 30))

        # Inputs
        self.master_pass_entry = ctk.CTkEntry(login_frame, placeholder_text="Master Password", show="*", width=300, height=40)
        self.master_pass_entry.pack(pady=10)

        self.username_entry = ctk.CTkEntry(login_frame, placeholder_text="Username", width=300, height=40)
        self.username_entry.pack(pady=10)

        self.otp_entry = ctk.CTkEntry(login_frame, placeholder_text="6-Digit OTP (from Mobile App)", width=300, height=40)
        self.otp_entry.pack(pady=10)

        # Login Button
        login_btn = ctk.CTkButton(login_frame, text="Authenticate & Unlock", command=self.login, width=300, height=45, font=("Roboto Medium", 14))
        login_btn.pack(pady=(20, 40))

        # Bind Enter keys
        self.master_pass_entry.bind("<Return>", lambda e: self.username_entry.focus())
        self.username_entry.bind("<Return>", lambda e: self.otp_entry.focus())
        self.otp_entry.bind("<Return>", lambda e: self.login())
        
        self.master_pass_entry.focus()

    def login(self):
        master_password = self.master_pass_entry.get()
        username = self.username_entry.get()
        otp = self.otp_entry.get()
        
        if not master_password or not username or not otp:
            self.show_error("Access Denied", "All fields are required.")
            return
        
        if len(otp) != 6 or not otp.isdigit():
            self.show_error("Access Denied", "OTP must be exactly 6 digits.")
            return
            
        # Verify MFA
        if not self.verify_mfa(username, otp):
            return
            
        # Load vault
        self.master_password = master_password
        if not self.load_vault():
            return
            
        self.show_main_screen()

    def verify_mfa(self, username, otp):
        try:
            import requests
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Show loading (optional, keeps UI responsive)
            self.root.update()
            
            response = requests.post(
                "https://127.0.0.1:5000/login",
                json={"username": username, "otp": otp},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("authenticated") is True:
                    return True
            
            error_msg = response.json().get('message', 'Authentication failed')
            if response.status_code == 404:
                self.show_error("MFA Error", f"User '{username}' not registered.\nPlease register in the Mobile App first.")
            elif response.status_code == 401:
                self.show_error("MFA Error", "Invalid or expired OTP.\nCodes expire after 60 seconds.")
            else:
                self.show_error("MFA Error", error_msg)
            return False
            
        except requests.exceptions.Timeout:
            self.show_error("Connection Error", "MFA Server timed out.\nIs the server running?")
            return False
        except requests.exceptions.ConnectionError:
            self.show_error("Connection Error", "Could not connect to MFA Server.\nPlease ensure mfa_server.py is running.")
            return False
        except Exception as e:
            self.show_error("System Error", f"MFA verification failed: {str(e)}")
            return False

    def load_vault(self):
        encrypted_data = self.file_manager.load_vault()
        
        if encrypted_data is False:
            self.show_error("CRITICAL ALEDT", "Vault file integrity compromised!\nFile has been tampered with.")
            sys.exit()
        elif encrypted_data is None:
            # New vault
            self.credentials = []
            messagebox.showinfo("Welcome", "Creating a new secure vault for you.")
            return True
        else:
            try:
                self.credentials = self.crypto.decrypt_data(encrypted_data, self.master_password)
                return True
            except Exception as e:
                self.show_error("Decryption Failed", f"Invalid Master Password or Corrupted Vault.\n\nDetails: {e}")
                return False

    def show_main_screen(self):
        self.clear_window()
        
        # Sidebar
        sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(sidebar, text="VaultGuard", font=("Roboto Medium", 22)).pack(pady=(30, 10))
        ctk.CTkLabel(sidebar, text=f"v2.0 Protected", text_color="gray", font=("Roboto", 10)).pack(pady=(0, 30))
        
        ctk.CTkButton(sidebar, text="Add Credential", command=self.add_credential_dialog, height=40, width=160).pack(pady=10)
        ctk.CTkButton(sidebar, text="Save & Lock", command=self.save_and_exit, height=40, width=160, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")).pack(pady=10, side="bottom")

        # Main Content Area
        content = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(content, text="My Safe Box", font=("Roboto Medium", 24)).pack(anchor="w", pady=(0, 20))
        
        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(content, label_text="Credentials")
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.refresh_list()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.credentials:
            ctk.CTkLabel(self.scroll_frame, text="No credentials stored yet.", text_color="gray").pack(pady=20)
            return

        for i, cred in enumerate(self.credentials):
            self.create_cred_card(i, cred)

    def create_cred_card(self, index, cred):
        card = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray25"))
        card.pack(fill="x", pady=5, padx=5)
        
        # Icon/Service Name
        ctk.CTkLabel(card, text="🔑", font=("Arial", 20)).pack(side="left", padx=(15, 5), pady=10)
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", padx=5)
        
        ctk.CTkLabel(info_frame, text=cred['service'], font=("Roboto Medium", 14)).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=cred['username'], font=("Roboto", 12), text_color="gray").pack(anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(btn_frame, text="Copy", width=60, height=25, command=lambda: self.copy_password(index)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Edit", width=60, height=25, fg_color="#E0a800", hover_color="#C09000", command=lambda: self.edit_credential_dialog(index)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Del", width=60, height=25, fg_color="#C0392b", hover_color="#A0291B", command=lambda: self.delete_credential(index)).pack(side="left", padx=2)
        
    def add_credential_dialog(self):
        self.show_cred_dialog("Add Credential")

    def edit_credential_dialog(self, index):
        cred = self.credentials[index]
        self.show_cred_dialog("Edit Credential", index, cred)

    def show_cred_dialog(self, title, index=None, cred=None):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x380")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=title, font=("Roboto Medium", 20)).pack(pady=20)
        
        entry_service = ctk.CTkEntry(dialog, placeholder_text="Service (e.g. Gmail)")
        entry_service.pack(pady=10, padx=20, fill="x")
        
        entry_username = ctk.CTkEntry(dialog, placeholder_text="Username")
        entry_username.pack(pady=10, padx=20, fill="x")
        
        entry_password = ctk.CTkEntry(dialog, placeholder_text="Password", show="*")
        entry_password.pack(pady=10, padx=20, fill="x")
        
        if cred:
            entry_service.insert(0, cred['service'])
            entry_username.insert(0, cred['username'])
            # We don't pre-fill password for security, or user can leave blank to keep
            entry_password.configure(placeholder_text="Enter new password to change")
            
        def save():
            s = entry_service.get().strip()
            u = entry_username.get().strip()
            p = entry_password.get()
            
            if not s or not u:
                self.show_error("Validation", "Service and Username are required.")
                return

            if index is not None:
                # Edit mode
                current_p = self.credentials[index]['password']
                final_p = p if p else current_p
                self.credentials[index] = {"service": s, "username": u, "password": final_p}
            else:
                # Add mode
                if not p:
                    self.show_error("Validation", "Password is required for new entries.")
                    return
                self.credentials.append({"service": s, "username": u, "password": p})
            
            self.refresh_list()
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Save Credential", command=save, height=40).pack(pady=20, padx=20, fill="x")

    def delete_credential(self, index):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this credential?"):
            del self.credentials[index]
            self.refresh_list()

    def copy_password(self, index):
        pwd = self.credentials[index]['password']
        self.root.clipboard_clear()
        self.root.clipboard_append(pwd)
        messagebox.showinfo("Copied", f"Password for {self.credentials[index]['service']} copied to clipboard!")

    def save_and_exit(self):
        if messagebox.askyesno("Save & Exit", "Encrypt and save your vault?"):
            try:
                encrypted = self.crypto.encrypt_data(self.credentials, self.master_password)
                self.file_manager.save_vault(encrypted)
                self.root.quit()
            except Exception as e:
                self.show_error("Save Failed", f"{str(e)}")

    def show_error(self, title, message):
        messagebox.showerror(title, message)

if __name__ == "__main__":
    root = ctk.CTk()
    app = VaultGUI(root)
    root.mainloop()
