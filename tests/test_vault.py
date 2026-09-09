import sys
import os
import unittest
import tempfile
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.vault_file_manager import VaultFileManager

class TestVaultFileManager(unittest.TestCase):
    """Test cases for Vault File Manager and Integrity"""
    
    def setUp(self):
        # Use temporary file for testing
        self.temp_vault = tempfile.NamedTemporaryFile(delete=False, suffix='.dat')
        self.temp_vault.close()
        self.vault_manager = VaultFileManager(filename=self.temp_vault.name)
    
    def tearDown(self):
        # Clean up temp file
        if os.path.exists(self.temp_vault.name):
            os.unlink(self.temp_vault.name)
    
    def test_save_and_load_vault(self):
        """Test saving and loading vault data"""
        test_data = b"encrypted_test_data"
        self.vault_manager.save_vault(test_data)
        loaded_data = self.vault_manager.load_vault()
        self.assertEqual(loaded_data, test_data)
    
    def test_load_nonexistent_vault(self):
        """Test loading vault that doesn't exist returns None"""
        os.unlink(self.temp_vault.name)
        result = self.vault_manager.load_vault()
        self.assertIsNone(result)
    
    def test_integrity_check(self):
        """Test integrity verification on vault file"""
        test_data = b"test_encrypted_data"
        self.vault_manager.save_vault(test_data)
        
        # Load should succeed with valid integrity
        loaded = self.vault_manager.load_vault()
        self.assertEqual(loaded, test_data)
    
    def test_tampered_vault_detected(self):
        """Test that tampered vault files are detected"""
        test_data = b"encrypted_data"
        self.vault_manager.save_vault(test_data)
        
        # Manually tamper with the file
        with open(self.temp_vault.name, 'r') as f:
            data = json.load(f)
        
        # Modify the hex data (change one character)
        original_data = data['data']
        # Change last character of hex string
        data['data'] = original_data[:-1] + ('0' if original_data[-1] != '0' else '1')
        
        with open(self.temp_vault.name, 'w') as f:
            json.dump(data, f)
        
        # Load should detect tampering
        result = self.vault_manager.load_vault()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
