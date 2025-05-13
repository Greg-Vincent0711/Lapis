import hashlib
import base64
# check SM for a key, etc
from lapis.encryption.key_generation import generate_fernet
from cryptography.fernet import Fernet

fernetInstance = Fernet(generate_fernet())

# provides a deterministic way to search for encrypted values in the DB
# cannot get data back with a hash though - irreversible
def generate_hash(userData: str) -> str:
    return hashlib.sha256(userData.lower().strip().encode()).hexdigest()

'''
Fernet encryption is not deterministic, so we can't directly query for encrypted data
before decrypting it. We can however use the stored key to get our data back consistently
'''
def encrypt(userData: str):
    # encrypt only takes binary data as a parameter, hence using encode
    return fernetInstance.encrypt(userData.encode())

def decrypt(encryptedData: str):
    return fernetInstance.decrypt(encryptedData)