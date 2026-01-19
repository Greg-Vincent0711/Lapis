'''
encryption.py and key_generation.py together encrypt/decrypt data in transit to DynamoDB and back
'''
import hashlib
from src.lapis.api.services.encryption.key_generation import generate_fernet
from cryptography.fernet import Fernet

# Cache the Fernet instance at module level (persists across Lambda invocations)
_fernet_instance = None

def getFernet():
    global _fernet_instance
    if _fernet_instance is None:
        print("Initializing Fernet instance")
        _fernet_instance = Fernet(generate_fernet())
    return _fernet_instance

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