import boto3
import os
from cryptography.fernet import Fernet

# generate a key if one does not exist


# assuming an encryption key doesn't exist
def generateKey():
    encryptionKey = checkForEncryptionKey()
    if encryptionKey:
        return encryptionKey
    else:
        encryptionKey = Fernet.generate_key()
        # add the key to secrets manager
        
        return encryptionKey

# check if an encyption key exists in secrets manager
def checkForEncryptionKey():
    pass