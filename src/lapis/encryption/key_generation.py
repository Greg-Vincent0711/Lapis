
import boto3
from botocore.exceptions import ClientError
import os
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
load_dotenv()


def getSMClient():
    session = boto3.session.Session()
    region = os.getenv("REGION_NAME")
    return session.client(service_name='secretsmanager',region_name=region)

def getSecretName():
    secret_name = os.getenv("SECRET_NAME")
    return secret_name

def get_secret_cache():
    sm_client = getSMClient()
    cache_config = SecretCacheConfig()
    return SecretCache(config=cache_config, client=sm_client)
'''
Generate a fernet key to encrypt client data in transit
Store in SM
'''
def generate_fernet():
    secret_name = getSecretName()
    encryptionKey = retrieve_fernet()
    if encryptionKey is not None:
        return encryptionKey
    else:
        encryptionKey = Fernet.generate_key().decode()
        # add the key to secrets manager
        response = smClient.create_secret(
            Name=secret_name,
            # SM only stores string types, not byte strings
            SecretString=f'{{"fernet_key": "{encryptionKey}"}}')
        print(f"Secret made. SM response: {response}")
        return encryptionKey

# check if the fernet secret exists and retrieve if so
def retrieve_fernet():
    secret_name = getSecretName()
    cache = get_secret_cache()
    smClient = getSMClient()
    try:
        print(f"Found secret for key.")
        retrieved_secret = json.loads(cache.get_secret_string(secret_name))
        return retrieved_secret.get("fernet_key")
    except smClient.exceptions.ResourceNotFoundException:
        print(f"A secret with the passed in key doesn't exist. Attempting to create...") 
        return None
    except ClientError as e:
        print(f"There was an outside error retrieving key: {e}")
        return None