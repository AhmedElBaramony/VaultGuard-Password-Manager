import sys
import os
import unittest
# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.crypto_manager import CryptoManager

class TestCryptoManager(unittest.TestCase):
    def setUp(self):
        self.crypto = CryptoManager()
        self.master_password = "secure_password_123"
        self.data = [{"service": "Gmail", "username": "bob", "password": "secret_password"}]

    def test_encrypt_decrypt(self):
        encrypted = self.crypto.encrypt_data(self.data, self.master_password)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, self.data)
        
        decrypted = self.crypto.decrypt_data(encrypted, self.master_password)
        self.assertEqual(decrypted, self.data)

    def test_wrong_password(self):
        encrypted = self.crypto.encrypt_data(self.data, self.master_password)
        with self.assertRaises(Exception):
            self.crypto.decrypt_data(encrypted, "wrong_password")

    def test_tampered_data(self):
        encrypted = bytearray(self.crypto.encrypt_data(self.data, self.master_password))
        # Modify the last byte (part of ciphertext or tag)
        encrypted[-1] ^= 0xFF
        with self.assertRaises(Exception):
            self.crypto.decrypt_data(bytes(encrypted), self.master_password)

if __name__ == '__main__':
    unittest.main()
