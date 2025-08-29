"""Cryptographic utilities for Deezer track decryption."""

from binascii import a2b_hex, b2a_hex
from hashlib import md5
from typing import BinaryIO

from Cryptodome.Cipher import Blowfish


def md5hex(data: bytes) -> bytes:
    """Calculate MD5 hash and return as hex bytes."""
    h = md5()
    h.update(data)
    return b2a_hex(h.digest())


def calculate_blowfish_key(track_id: str) -> str:
    """Calculate the Blowfish decrypt key for a given track ID.
    
    Args:
        track_id: Deezer track ID as string
        
    Returns:
        16-character decryption key
    """
    key = b"g4el58wc0zvf9na1"
    track_id_md5 = md5hex(track_id.encode())
    
    # XOR operation to generate decrypt key
    xor_op = lambda i: chr(track_id_md5[i] ^ track_id_md5[i + 16] ^ key[i])
    decrypt_key = "".join([xor_op(i) for i in range(16)])
    
    return decrypt_key


def blowfish_decrypt(data: bytes, key: str) -> bytes:
    """Decrypt data using Blowfish cipher.
    
    Args:
        data: Encrypted data bytes
        key: Decryption key string
        
    Returns:
        Decrypted data bytes
    """
    iv = a2b_hex("0001020304050607")
    cipher = Blowfish.new(key.encode(), Blowfish.MODE_CBC, iv)
    return cipher.decrypt(data)


def decrypt_track_stream(input_stream, output_file: BinaryIO, key: str) -> None:
    """Decrypt a Deezer track stream and write to output file.
    
    Deezer encrypts every third 2048-byte block using Blowfish.
    
    Args:
        input_stream: Response stream from Deezer
        output_file: Binary file handle to write decrypted data
        key: Blowfish decryption key
    """
    block_size = 2048
    block_index = 0
    
    for data in input_stream.iter_content(block_size):
        if not data:
            break
            
        # Only every third block is encrypted
        is_encrypted = (block_index % 3) == 0
        is_whole_block = len(data) == block_size
        
        if is_encrypted and is_whole_block:
            data = blowfish_decrypt(data, key)
            
        output_file.write(data)
        block_index += 1