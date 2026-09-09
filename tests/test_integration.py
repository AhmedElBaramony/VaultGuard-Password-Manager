import sys
import os
import unittest
import tempfile

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.crypto_manager import CryptoManager
from src.core.vault_file_manager import VaultFileManager

class TestIntegration(unittest.TestCase):
    """Integration tests for complete encryption/decryption workflow"""
    
    def setUp(self):
        self.crypto = CryptoManager()
        self.temp_vault = tempfile.NamedTemporaryFile(delete=False, suffix='.dat')
        self.temp_vault.close()
        self.vault_manager = VaultFileManager(filename=self.temp_vault.name)
        self.master_password = "MySecureMasterPassword123!"
        self.credentials = [
            {"service": "Gmail", "username": "user@gmail.com", "password": "gmail_pass_123"},
            {"service": "GitHub", "username": "developer", "password": "github_token_xyz"}
        ]
    
    def tearDown(self):
        if os.path.exists(self.temp_vault.name):
            os.unlink(self.temp_vault.name)
    
    def test_full_encryption_decryption_workflow(self):
        """Test complete workflow: encrypt -> save -> load -> decrypt"""
        # Encrypt data
        encrypted = self.crypto.encrypt_data(self.credentials, self.master_password)
        self.assertIsNotNone(encrypted)
        
        # Save to vault
        self.vault_manager.save_vault(encrypted)
        
        # Load from vault
        loaded_encrypted = self.vault_manager.load_vault()
        self.assertEqual(loaded_encrypted, encrypted)
        
        # Decrypt data
        decrypted = self.crypto.decrypt_data(loaded_encrypted, self.master_password)
        self.assertEqual(decrypted, self.credentials)
    
    def test_wrong_password_fails(self):
        """Test that wrong password fails decryption"""
        encrypted = self.crypto.encrypt_data(self.credentials, self.master_password)
        
        with self.assertRaises(Exception):
            self.crypto.decrypt_data(encrypted, "wrong_password")
    
    def test_data_integrity_preserved(self):
        """Test that data integrity is preserved through encryption"""
        encrypted = self.crypto.encrypt_data(self.credentials, self.master_password)
        self.vault_manager.save_vault(encrypted)
        
        loaded = self.vault_manager.load_vault()
        decrypted = self.crypto.decrypt_data(loaded, self.master_password)
        
        # Verify all fields preserved
        self.assertEqual(len(decrypted), len(self.credentials))
        for original, restored in zip(self.credentials, decrypted):
            self.assertEqual(original['service'], restored['service'])
            self.assertEqual(original['username'], restored['username'])
            self.assertEqual(original['password'], restored['password'])

if __name__ == '__main__':
    unittest.main()
