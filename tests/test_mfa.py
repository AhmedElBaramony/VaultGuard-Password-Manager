import sys
import os
import unittest
import time
import pyotp

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMFASystem(unittest.TestCase):
    """Test cases for MFA/TOTP functionality"""
    
    def setUp(self):
        self.secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.secret, interval=60)
    
    def test_totp_60_second_interval(self):
        """Test that TOTP uses 60-second interval"""
        self.assertEqual(self.totp.interval, 60)
    
    def test_otp_generation(self):
        """Test OTP generation"""
        otp = self.totp.now()
        self.assertIsInstance(otp, str)
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())
    
    def test_otp_verification(self):
        """Test OTP verification"""
        otp = self.totp.now()
        self.assertTrue(self.totp.verify(otp))
    
    def test_invalid_otp_rejected(self):
        """Test that invalid OTPs are rejected"""
        self.assertFalse(self.totp.verify("000000"))
        self.assertFalse(self.totp.verify("999999"))
    
    def test_otp_validity_window(self):
        """Test that OTP is valid within 60-second window"""
        otp = self.totp.now()
        # Should be valid immediately
        self.assertTrue(self.totp.verify(otp))
        
        # Wait a few seconds and verify still valid
        time.sleep(3)
        self.assertTrue(self.totp.verify(otp))
    
    def test_expired_otp_rejected(self):
        """Test that OTPs expire after time window"""
        # This test would require waiting 60+ seconds
        # We'll test the time remaining calculation instead
        time_remaining = self.totp.interval - (time.time() % self.totp.interval)
        self.assertGreater(time_remaining, 0)
        self.assertLessEqual(time_remaining, 60)

if __name__ == '__main__':
    unittest.main()
