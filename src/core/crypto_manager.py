"""
Cryptography Module for VaultGuard Password Manager

This module provides:
- Master Password authentication using Argon2 KDF
- AES-256-GCM encryption for vault data
- Salted password hashing with Argon2
"""

import os
import json
import hashlib
import hmac
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2 import PasswordHasher
from argon2.low_level import hash_secret_raw, Type


class CryptoManager:
    """
    Handles all cryptographic operations for the VaultGuard application.
    """
    
    def __init__(self):
        # Argon2 password hasher with secure defaults
        self.ph = PasswordHasher(
            time_cost=3,        # Number of iterations
            memory_cost=65536,  # 64 MB memory
            parallelism=4,      # Number of parallel threads
            hash_len=32,        # 32 bytes = 256 bits
            salt_len=16         # 16 bytes salt
        )
    
    def hash_master_password(self, password: str) -> str:
        """
        Hash the master password using Argon2id for secure storage.
        
        Args:
            password: The master password string
            
        Returns:
            Argon2 hash string (includes salt and parameters)
        """
        return self.ph.hash(password)
    
    def verify_master_password(self, password: str, hash_string: str) -> bool:
        """
        Verify a master password against its hash.
        
        Args:
            password: The password to verify
            hash_string: The stored Argon2 hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            self.ph.verify(hash_string, password)
            return True
        except:
            return False
    
    def derive_encryption_key(self, password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """
        Derive a 256-bit encryption key from the master password using Argon2.
        
        Args:
            password: The master password
            salt: Optional salt (generates new one if not provided)
            
        Returns:
            Tuple of (encryption_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)  # Generate 16-byte random salt
        
        # Derive key using Argon2id
        key = hash_secret_raw(
            secret=password.encode('utf-8'),
            salt=salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=Type.ID  # Argon2id - hybrid version (recommended)
        )
        
        return key, salt
    
    def encrypt_vault_data(self, plaintext: str, encryption_key: bytes) -> dict:
        """
        Encrypt vault data using AES-256-GCM.
        
        Args:
            plaintext: The data to encrypt (JSON string)
            encryption_key: 32-byte encryption key
            
        Returns:
            Dictionary containing encrypted data, nonce, and tag
        """
        # Generate a random 96-bit nonce (12 bytes recommended for GCM)
        nonce = os.urandom(12)
        
        # Create AES-GCM cipher
        aesgcm = AESGCM(encryption_key)
        
        # Encrypt the data (GCM provides authentication automatically)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Return encrypted data with metadata
        return {
            'ciphertext': b64encode(ciphertext).decode('utf-8'),
            'nonce': b64encode(nonce).decode('utf-8')
        }
    
    def decrypt_vault_data(self, encrypted_data: dict, encryption_key: bytes) -> str:
        """
        Decrypt vault data using AES-256-GCM.
        
        Args:
            encrypted_data: Dictionary with ciphertext and nonce
            encryption_key: 32-byte encryption key
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            Exception if decryption fails (wrong key or tampered data)
        """
        try:
            # Decode base64 encoded data
            ciphertext = b64decode(encrypted_data['ciphertext'])
            nonce = b64decode(encrypted_data['nonce'])
            
            # Create AES-GCM cipher
            aesgcm = AESGCM(encryption_key)
            
            # Decrypt and verify authentication tag
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            raise Exception("Decryption failed: Invalid key or corrupted data")
    
    def compute_file_integrity_hash(self, file_data: dict) -> str:
        """
        Compute SHA-256 hash of vault file data for integrity verification.
        
        Args:
            file_data: Dictionary containing vault file data (without 'integrity_hash' field)
            
        Returns:
            SHA-256 hash as hex string
        """
        # Create deterministic JSON string (sorted keys for consistency)
        json_data = json.dumps(file_data, sort_keys=True)
        
        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(json_data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def verify_file_integrity(self, file_data: dict) -> bool:
        """
        Verify the integrity hash of a vault file.
        
        Args:
            file_data: Dictionary loaded from vault file (includes 'integrity_hash')
            
        Returns:
            True if integrity check passes, False otherwise
        """
        # Extract the stored hash
        stored_hash = file_data.get('integrity_hash')
        if not stored_hash:
            return False
        
        # Create a copy without the hash field
        data_without_hash = {k: v for k, v in file_data.items() if k != 'integrity_hash'}
        
        # Compute expected hash
        computed_hash = self.compute_file_integrity_hash(data_without_hash)
        
        # Compare hashes (constant-time comparison to prevent timing attacks)
        return hmac.compare_digest(stored_hash, computed_hash)
    
    def create_vault_file_data(self, vault_data: dict, master_password: str) -> dict:
        """
        Complete encryption workflow: hash password, derive key, encrypt data, add integrity hash.
        
        Args:
            vault_data: Dictionary containing vault credentials
            master_password: The master password
            
        Returns:
            Dictionary ready to be saved to disk
        """
        # 1. Hash the master password for verification
        password_hash = self.hash_master_password(master_password)
        
        # 2. Derive encryption key from master password
        encryption_key, salt = self.derive_encryption_key(master_password)
        
        # 3. Convert vault data to JSON
        vault_json = json.dumps(vault_data)
        
        # 4. Encrypt the vault data
        encrypted = self.encrypt_vault_data(vault_json, encryption_key)
        
        # 5. Prepare file structure (without integrity hash first)
        file_data = {
            'password_hash': password_hash,
            'salt': b64encode(salt).decode('utf-8'),
            'encrypted_data': encrypted
        }
        
        # 6. Compute and add SHA-256 integrity hash
        integrity_hash = self.compute_file_integrity_hash(file_data)
        file_data['integrity_hash'] = integrity_hash
        
        return file_data
    
    def unlock_vault_file_data(self, file_data: dict, master_password: str) -> dict:
        """
        Complete decryption workflow: verify integrity, verify password, derive key, decrypt data.
        
        Args:
            file_data: Dictionary loaded from vault file
            master_password: The master password to try
            
        Returns:
            Dictionary containing decrypted vault credentials
            
        Raises:
            Exception if integrity check fails, password is incorrect, or data is corrupted
        """
        # 1. Verify file integrity (SHA-256 hash)
        if not self.verify_file_integrity(file_data):
            raise Exception("Integrity check failed: Vault file has been tampered with or corrupted")
        
        # 2. Verify master password
        if not self.verify_master_password(master_password, file_data['password_hash']):
            raise Exception("Invalid master password")
        
        # 3. Derive encryption key using stored salt
        salt = b64decode(file_data['salt'])
        encryption_key, _ = self.derive_encryption_key(master_password, salt)
        
        # 4. Decrypt the vault data
        decrypted_json = self.decrypt_vault_data(file_data['encrypted_data'], encryption_key)
        
        # 5. Parse and return vault data
        return json.loads(decrypted_json)
    
    # ===== Interface Methods for VaultGuard Application Integration =====
    
    def encrypt_data(self, credentials: list, master_password: str) -> bytes:
        """
        Interface method for VaultGuard app integration.
        Wrapper around create_vault_file_data() for compatibility.
        
        Args:
            credentials: List of credential dictionaries
            master_password: The master password
            
        Returns:
            Encrypted vault file data as bytes (JSON encoded)
        """
        vault_data = {"credentials": credentials}
        file_data = self.create_vault_file_data(vault_data, master_password)
        # Convert dict to JSON bytes for vault_file_manager
        return json.dumps(file_data).encode('utf-8')
    
    def decrypt_data(self, encrypted_data, master_password: str) -> list:
        """
        Interface method for VaultGuard app integration.
        Wrapper around unlock_vault_file_data() for compatibility.
        
        Args:
            encrypted_data: Encrypted vault file data (can be dict, bytes, or str)
            master_password: The master password
            
        Returns:
            List of credential dictionaries
            
        Raises:
            Exception if decryption fails
        """
        # Handle different input types from vault_file_manager
        if isinstance(encrypted_data, bytes):
            # If bytes, decode to JSON string first, then parse
            try:
                encrypted_data = json.loads(encrypted_data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise Exception(f"Failed to parse encrypted data: {e}")
        elif isinstance(encrypted_data, str):
            # If string, parse as JSON
            try:
                encrypted_data = json.loads(encrypted_data)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse encrypted data: {e}")
        
        # Check if this is legacy unencrypted data (list format)
        if isinstance(encrypted_data, list):
            raise Exception(
                "Legacy vault format detected. The vault file uses an old unencrypted format. "
                "Please delete 'vault.dat' and create a new vault with proper encryption."
            )
        
        # Ensure we have a dictionary at this point
        if not isinstance(encrypted_data, dict):
            raise Exception(f"Invalid encrypted data format. Expected dict, got {type(encrypted_data).__name__}")
        
        # Check if required fields are present
        required_fields = ['password_hash', 'salt', 'encrypted_data', 'integrity_hash']
        missing_fields = [field for field in required_fields if field not in encrypted_data]
        if missing_fields:
            raise Exception(
                f"Invalid vault file format. Missing required fields: {', '.join(missing_fields)}. "
                "The vault may be corrupted or use an incompatible format. "
                "Consider deleting 'vault.dat' and creating a new vault."
            )
        
        vault_data = self.unlock_vault_file_data(encrypted_data, master_password)
        return vault_data.get("credentials", [])
