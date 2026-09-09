import sys
import os
import unittest

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.crypto_manager import CryptoManager

class TestArgon2KDF(unittest.TestCase):
    """Test cases for Argon2 Key Derivation Function"""
    
    def setUp(self):
        self.crypto = CryptoManager()
        self.password = "secure_master_password_123"
    
    def test_hash_master_password(self):
        """Test Argon2 password hashing"""
        hash1 = self.crypto.hash_master_password(self.password)
        self.assertIsInstance(hash1, str)
        self.assertIn("$argon2", hash1)
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        hash1 = self.crypto.hash_master_password("password1")
        hash2 = self.crypto.hash_master_password("password2")
        self.assertNotEqual(hash1, hash2)
    
    def test_same_password_different_hashes_due_to_salt(self):
        """Test that same password produces different hashes (due to salt)"""
        hash1 = self.crypto.hash_master_password(self.password)
        hash2 = self.crypto.hash_master_password(self.password)
        self.assertNotEqual(hash1, hash2)
    
    def test_verify_correct_password(self):
        """Test verifying correct password"""
        hash_value = self.crypto.hash_master_password(self.password)
        self.assertTrue(self.crypto.verify_master_password(self.password, hash_value))
    
    def test_verify_wrong_password(self):
        """Test rejecting wrong password"""
        hash_value = self.crypto.hash_master_password(self.password)
        self.assertFalse(self.crypto.verify_master_password("wrong_password", hash_value))
    
    def test_key_derivation(self):
        """Test Argon2 key derivation"""
        key1, salt1 = self.crypto.derive_encryption_key(self.password)
        self.assertEqual(len(key1), 32)  # 256 bits = 32 bytes
        self.assertEqual(len(salt1), 16)  # 16 bytes salt
    
    def test_same_password_same_salt_same_key(self):
        """Test deterministic key derivation with same salt"""
        key1, salt = self.crypto.derive_encryption_key(self.password)
        key2, _ = self.crypto.derive_encryption_key(self.password, salt)
        self.assertEqual(key1, key2)
    
    def test_different_salt_different_key(self):
        """Test different salts produce different keys"""
        key1, salt1 = self.crypto.derive_encryption_key(self.password)
        key2, salt2 = self.crypto.derive_encryption_key(self.password)
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(salt1, salt2)

if __name__ == '__main__':
    unittest.main()
