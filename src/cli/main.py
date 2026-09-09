import getpass
import sys
import time
import os
import sys

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.vault_file_manager import VaultFileManager
from src.core.crypto_manager import CryptoManager
from src.auth.mfa_client import MFAService

# Try to import pyperclip, but don't crash if it's missing
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

class VaultGuardClient:
    def __init__(self):
        self.file_manager = VaultFileManager()
        self.crypto = CryptoManager()
        self.mfa = MFAService()
        self.credentials = []
        self.master_password = None

    def start(self):
        print("="*50)
        print("     VaultGuard: Secure Password Vault")
        print("="*50)

        # 1. Master Password Input
        self.master_password = getpass.getpass("Enter Master Password: ")
        
        # 2. MFA Authentication
        if not self.mfa.perform_login():
            print("[Access Denied] MFA Failed.")
            sys.exit()

        # 3. Load Data (Member 1 & 2 Integration)
        encrypted_data = self.file_manager.load_vault()
        
        if encrypted_data is False:
            print("[Security Alert] File integrity compromised. Exiting.")
            sys.exit()
        elif encrypted_data is None:
            print("[System] Creating a new empty vault.")
            self.credentials = []
        else:

            try:
                self.credentials = self.crypto.decrypt_data(encrypted_data, self.master_password)
            except Exception as e:
                print(f"[Error] Access Denied: {e}")
                print("[Hint] If you forgot your password or want to start fresh, delete 'vault.dat'.")
                sys.exit()

        self.main_menu()

    def main_menu(self):
        while True:
            print("\n--- Main Menu ---")
            print("1. View Credentials")
            print("2. Add Credential")
            print("3. Edit Credential")
            print("4. Copy Password")
            print("5. Save & Exit")
            
            choice = input("Select: ")

            if choice == '1': self.view_credentials()
            elif choice == '2': self.add_credential()
            elif choice == '3': self.edit_credential()
            elif choice == '4': self.copy_credential()
            elif choice == '5': 
                self.save_vault()
                break
            else: print("Invalid selection.")

    def view_credentials(self):
        if not self.credentials:
            print("\n[Vault is empty]")
            return
        print(f"\n{'ID':<4} | {'Service':<15} | {'Username'}")
        print("-" * 40)
        for i, cred in enumerate(self.credentials):
            print(f"{i:<4} | {cred['service']:<15} | {cred['username']}")

    def add_credential(self):
        print("\n[Add New Credential]")
        service = input("Service: ")
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        self.credentials.append({"service": service, "username": username, "password": password})
        print("[Success] Added.")

    def edit_credential(self):
        self.view_credentials()
        try:
            idx = int(input("ID to edit: "))
            if 0 <= idx < len(self.credentials):
                item = self.credentials[idx]
                print(f"Editing {item['service']} (Leave blank to keep current)")
                
                s = input(f"Service [{item['service']}]: ") or item['service']
                u = input(f"Username [{item['username']}]: ") or item['username']
                p = getpass.getpass("Password (hidden): ") or item['password']
                
                self.credentials[idx] = {"service": s, "username": u, "password": p}
                print("[Success] Updated.")
        except ValueError:
            print("[Error] Invalid ID.")

    def copy_credential(self):
        self.view_credentials()
        try:
            idx = int(input("ID to copy password: "))
            if 0 <= idx < len(self.credentials):
                pwd = self.credentials[idx]['password']
                if HAS_CLIPBOARD:
                    pyperclip.copy(pwd)
                    print(f"[Success] Password for '{self.credentials[idx]['service']}' copied to clipboard.")
                else:
                    print(f"[Result] Password is: {pwd}")
                    print("(Install 'pyperclip' to hide this and copy to clipboard instead)")
        except ValueError:
            print("[Error] Invalid input.")

    def save_vault(self):
        print("\n[System] Encrypting and saving...")
        # Member 2 encrypts
        encrypted = self.crypto.encrypt_data(self.credentials, self.master_password)
        # Member 1 saves with integrity check
        self.file_manager.save_vault(encrypted)
        print("[System] Done. Exiting.")

if __name__ == "__main__":
    VaultGuardClient().start()