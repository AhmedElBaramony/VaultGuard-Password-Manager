# FILE: vault_file_manager.py
import json
import hashlib
import os

class VaultFileManager:
    """
    Handles reading/writing the vault file and verifying integrity.
    """
    def __init__(self, filename=None):
        if filename:
            self.filename = filename
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.filename = os.path.join(base_dir, 'data', 'vault.dat')

    def _calculate_checksum(self, data_bytes):
        """
        Internal method to generate SHA-256 hash for integrity checks.
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(data_bytes)
        return sha256_hash.hexdigest()

    def save_vault(self, ciphertext_bytes):
        """
        Saves the encrypted data + integrity hash to a JSON file.
        """
        checksum = self._calculate_checksum(ciphertext_bytes)
        
        # Structure defined to hold both data and security check
        storage_packet = {
            "integrity_hash": checksum,
            "data": ciphertext_bytes.hex()  # Convert bytes to hex string for JSON
        }
        
        try:
            with open(self.filename, 'w') as f:
                json.dump(storage_packet, f)
            print(f"[System] Vault saved securely to '{self.filename}'.")
            return True
        except IOError as e:
            print(f"[Error] Failed to save vault: {e}")
            return False

    def load_vault(self):
        """
        Loads the file and performs the Critical Integrity Check.
        Returns: bytes (if successful), None (if file missing), or False (if tampered).
        """
        if not os.path.exists(self.filename):
            print("[System] No existing vault found.")
            return None

        try:
            with open(self.filename, 'r') as f:
                storage_packet = json.load(f)
            
            stored_hash = storage_packet.get('integrity_hash')
            data_hex = storage_packet.get('data')
            
            if not stored_hash or not data_hex:
                print("[Error] Vault file format is invalid.")
                return False

            ciphertext_bytes = bytes.fromhex(data_hex)
            
            # --- INTEGRITY CHECK ---
            calculated_hash = self._calculate_checksum(ciphertext_bytes)
            
            if calculated_hash != stored_hash:
                print("\n[CRITICAL SECURITY WARNING] INTEGRITY CHECK FAILED!")
                print("[System] The vault file has been modified externally.")
                return False # Return False to signal tampering
            
            print("[System] Integrity check passed (SHA-256 verified).")
            return ciphertext_bytes

        except (json.JSONDecodeError, IOError) as e:
            print(f"[Error] Failed to load vault: {e}")
            return False