import requests
import pyotp
import time
import sys
import urllib3

# Suppress warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MobileAuthApp:
    def __init__(self):
        self.server_url = "https://127.0.0.1:5000"
        self.username = None
        self.secret = None
        
    def start(self):
        print("\n=== VaultGuard Mobile Authenticator ===")
        while True:
            if not self.secret:
                print("\n1. Register New Device")
                print("2. Recover/Enter Existing Secret")
                print("3. Exit")
            else:
                print(f"\nUser: {self.username}")
                print("1. Show Current OTP")
                print("2. Reset/Logout")
                print("3. Exit")
                
            choice = input("Select: ")
            
            if not self.secret:
                if choice == '1': self.register()
                elif choice == '2': self.manual_entry()
                elif choice == '3': sys.exit()
            else:
                if choice == '1': self.show_otp()
                elif choice == '2': self.reset()
                elif choice == '3': sys.exit()

    def register(self):
        username = input("Enter Username to Register: ")
        try:
            # Note: verify=False because using self-signed certs
            response = requests.post(
                f"{self.server_url}/register", 
                json={"username": username},
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                self.secret = data['secret']
                self.username = username
                print(f"\n[Success] Registered! Secret: {self.secret}")
                print("This device is now linked.")
            elif response.status_code == 409:
                print("\n[Error] User already exists.")
            else:
                print(f"\n[Error] Server returned: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("\n[Error] Could not connect to MFA Server. Is it running?")

    def manual_entry(self):
        self.username = input("Username: ")
        secret = input("Secret (Base32): ").strip().replace(" ", "")
        
        # Simple validation
        try:
            import base64
            base64.b32decode(secret, casefold=True)
            self.secret = secret
            print("[Info] Secret saved locally.")
        except Exception:
            print("[Error] Invalid Base32 Secret! (Don't use the Debugger PIN)")
            self.secret = None

    def show_otp(self):
        if not self.secret:
            print("No secret found.")
            return
            
        totp = pyotp.TOTP(self.secret, interval=60)  # 60-second interval as per requirements
        otp = totp.now()
        remaining = totp.interval - (time.time() % totp.interval)
        
        print(f"\n>>> CURRENT OTP: {otp} <<<")
        print(f"(Valid for {int(remaining)} more seconds)")
        
        # Live update simulation
        # In a real GUI this would update automatically
        print("\nPress Enter to return...")
        input()

    def reset(self):
        self.secret = None
        self.username = None
        print("App reset.")

if __name__ == "__main__":
    try:
        MobileAuthApp().start()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Application crashed: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close window...")
