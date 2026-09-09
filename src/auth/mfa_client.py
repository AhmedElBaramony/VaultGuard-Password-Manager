import requests
import getpass
import urllib3

# Suppress warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MFAService:
    """
    Handles communication with the MFA Server from the VaultGuard Client.
    """
    def __init__(self):
        self.server_url = "https://127.0.0.1:5000"

    def perform_login(self):
        """
        Interactive login flow:
        1. Ask for Username
        2. Ask for OTP
        3. Validate with Server
        """
        print("\n--- MFA Login Required ---")
        username = input("Username: ")
        # In a real scenario, the username might come from the vault, 
        # but for this project structure, we authenticate the session first.
        
        otp = input("Enter OTP from Mobile App: ")
        
        try:
            print("[System] Verifying with MFA Server...")
            response = requests.post(
                f"{self.server_url}/login",
                json={"username": username, "otp": otp},
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("authenticated") is True:
                    print("[Success] MFA Authentication Successful.")
                    return True
            
            print(f"[Access Denied] {response.json().get('message', 'Unknown Error')}")
            return False

        except requests.exceptions.ConnectionError:
            print("\n[CRITICAL ERROR] Could not connect to MFA Server.")
            print("Ensure 'mfa_server.py' is running.")
            return False
