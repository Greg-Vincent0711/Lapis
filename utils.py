import boto3
import os
from cryptography.fernet import Fernet

secretsManagerInstance = boto3.resource('secretsmanager')

def storeKey(fernetKey):
    try:
        response = secretsManagerInstance.create_secret(
            Name=os.getenv('KEY_NAME'),
            SecretString=fernetKey
        )

        print(f"Key {fernetKey} has been stored: {response}")
    except Exception as e:
        print(f"Error storing key in Secrets Manager: {e}")
        
def getKey(secret_name):
    try:
        response = secretsManagerInstance.get_secret_value(
            SecretId=secret_name
        )
        fernetKeyString = response['SecretString']
        return fernetKeyString.encode('utf-8')
    except Exception as e:
        print(f"Error retrieving key from Secrets Manager: {e}")
        return None
        


# # Generate a new Fernet key (this key would normally be generated only once)
# key = Fernet.generate_key()

# # Store the key securely in AWS Secrets Manager
# store_key_in_secrets_manager('my-encryption-key', key)

# # Retrieve the key back from Secrets Manager
# retrieved_key = get_key_from_secrets_manager('my-encryption-key')

# if retrieved_key:
#     # Now, use the retrieved key for encryption/decryption
#     fernet = Fernet(retrieved_key)

#     # Encrypt some data
#     data = "This is some sensitive data."
#     encrypted_data = fernet.encrypt(data.encode('utf-8'))
#     print(f"Encrypted Data: {encrypted_data}")

#     # Decrypt the data
#     decrypted_data = fernet.decrypt(encrypted_data).decode('utf-8')
#     print(f"Decrypted Data: {decrypted_data}")
