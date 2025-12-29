'''
encryption.py and key_generation.py together encrypt/decrypt set in transit to DynamoDB and back
'''
import hashlib
# check SM for a key, etc
from src.lapis.api.services.encryption.key_generation import generate_fernet
from cryptography.fernet import Fernet

def getFernet():
    fernetInstance = Fernet(generate_fernet())
    return fernetInstance

# provides a deterministic way to search for encrypted values in the DB
# cannot get data back with a hash though - irreversible
def generate_hash(userData: str) -> str:
    return hashlib.sha256(userData.lower().strip().encode()).hexdigest()

'''
Fernet encryption is not deterministic, so we can't directly query for encrypted data
before decrypting it. We can however use the stored key to get our data back consistently
'''
def encrypt(userData: str):
    fernetInstance = getFernet()
    # encrypt only takes binary data as a parameter, hence using encode
    return fernetInstance.encrypt(userData.encode())

def decrypt(encryptedData: str | bytes):
    fernetInstance = getFernet()
    if isinstance(encryptedData, str):
        encryptedData = encryptedData.encode()
    return fernetInstance.decrypt(encryptedData)