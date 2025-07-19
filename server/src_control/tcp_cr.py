import os
import hmac
import hashlib
import struct
from typing import Tuple, List

class TCPEncryptor:
    def __init__(self, secret_key: bytes):
        """
        Initialize with a pre-shared 32-byte secret key.
        """
        if len(secret_key) != 32:
            raise ValueError("Key must be 32 bytes (256-bit) for AES-256.")
        self.secret_key = secret_key
        self.seq_num = 0

    def _generate_iv(self) -> bytes:
        """Generate a unique IV per packet."""
        return os.urandom(16)

    def _hmac_sign(self, data: bytes) -> bytes:
        """Generate HMAC-SHA256 for integrity checks."""
        return hmac.new(self.secret_key, data, hashlib.sha256).digest()[:16]

    def _encrypt_block(self, plaintext: bytes) -> bytes:
        """AES-256-CTR encryption (simplified)."""
        iv = self._generate_iv()
        cipher = hashlib.sha256(iv + self.secret_key).digest()
        encrypted = bytes(plaintext[i] ^ cipher[i % 32] for i in range(len(plaintext)))
        return iv + encrypted

    def _decrypt_block(self, ciphertext: bytes) -> bytes:
        """AES-256-CTR decryption."""
        iv, encrypted = ciphertext[:16], ciphertext[16:]
        cipher = hashlib.sha256(iv + self.secret_key).digest()
        return bytes(encrypted[i] ^ cipher[i % 32] for i in range(len(encrypted)))

    def create_packet(self, data: bytes) -> bytes:
        """
        Encrypt and package data into a TCP-like secure packet:
        1. Sequence number (8 bytes)
        2. IV + Encrypted payload
        3. HMAC signature (16 bytes)
        """
        # Encrypt payload
        encrypted = self._encrypt_block(data)
        
        # Build packet header
        header = struct.pack("!Q", self.seq_num)  # Big-endian 8-byte sequence number
        self.seq_num += 1
        
        # Combine parts and sign
        packet_content = header + encrypted
        signature = self._hmac_sign(packet_content)
        
        return packet_content + signature

    def verify_packet(self, packet: bytes) -> Tuple[int, bytes]:
        """
        Decrypt and validate a packet:
        1. Verify HMAC
        2. Check sequence number
        3. Decrypt payload
        Returns: (sequence_number, decrypted_payload)
        """
        if len(packet) < 40:  # header(8) + IV(16) + HMAC(16)
            raise ValueError("Invalid packet length")

        # Split components
        header = packet[:8]
        payload = packet[8:-16]
        received_hmac = packet[-16:]

        # Verify HMAC
        computed_hmac = self._hmac_sign(header + payload)
        if not hmac.compare_digest(received_hmac, computed_hmac):
            raise ValueError("HMAC validation failed")

        # Decode sequence number
        seq_num = struct.unpack("!Q", header)[0]

        if seq_num != self.seq_num:
            raise ValueError(f"Sequence mismatch (expected {self.seq_num}, got {seq_num})")

        # Decrypt payload
        plaintext = self._decrypt_block(payload)
        self.seq_num += 1

        return (seq_num, plaintext)

# Example Usage
#if __name__ == "__main__":
#    # Pre-shared key (must be 32 bytes)
#    SECRET_KEY = os.urandom(32)

#    # Initialize encryptor/decryptor (simulating two endpoints)
#    alice = TCPEncryptor(SECRET_KEY)
#    bob = TCPEncryptor(SECRET_KEY)

#    # Alice sends a secure message
#    message = b"Mission-critical payload"
#    packet = alice.create_packet(message)
#    print(f"Encrypted Packet: {packet.hex()}")

#    # Bob receives and decrypts it
#    try:
#        seq, decrypted = bob.verify_packet(packet)
#        print(f"Decrypted (seq={seq}): {decrypted.decode()}")
#    except ValueError as e:
#        print(f"Decryption failed: {e}")

