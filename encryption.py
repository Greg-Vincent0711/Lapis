
# check from SM for a key, etc
from key_generation import generate_fernet
from cryptography.fernet import Fernet

fernetInstance = Fernet(generate_fernet())

def encrypt(userData: str):
    # encrypt only takes binary data as a parameter
    return fernetInstance.encrypt(userData.encode())

def decrypt(encryptedData: bytes):
    return fernetInstance.decrypt(encryptedData.decode())