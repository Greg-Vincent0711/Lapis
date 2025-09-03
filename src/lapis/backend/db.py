import boto3
from botocore.exceptions import ClientError
from src.lapis.backend.s3_fns import storeImageInS3, deleteImage
from src.lapis.encryption.encryption import encrypt, decrypt, generate_hash
from src.lapis.helpers.utils import extract_decrypted_locations
import os


'''
Updating code so that env retrieval is at run time instead of import time
This is to fix a bug with Github Actions tests on push
'''
def get_table():
    dbInstance = boto3.resource('dynamodb', region_name=os.getenv("REGION_NAME"))
    TABLE = dbInstance.Table(os.getenv('TABLE_NAME'))
    return TABLE

# add or completely replace an item
def save_location(author_id, location_name, coords):
    TABLE = get_table()
    res = TABLE.put_item(
        Item={
            "Author_ID": str(author_id),
            "Location": generate_hash(location_name),
            "Location_Name": encrypt(location_name).decode(),
            "Coordinates": encrypt(coords).decode(),
        }
    )
    status = res.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status != 200:
        raise Exception(f"Putting your item failed with status code {status}. Try again later.")
    

def get_location(author_id, location_name):
    TABLE = get_table()
    try:
        res = TABLE.get_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            }
        )
        if 'Item' in res:
            encryptedCoordinates = res['Item']['Coordinates']
            retrieved_coordinates = decrypt(encryptedCoordinates.encode()).decode()
            if res['Item'].get("Image_URL"):
                encryptedURL = res['Item']['Image_URL']
                retrieved_URL = decrypt(encryptedURL.encode()).decode()
                return [retrieved_coordinates, retrieved_URL]
            else:
                return [retrieved_coordinates]
        else: 
            return None
    
    except ClientError:
        raise

def delete_location(author_id, location_name):
    TABLE = get_table()
    try:
        res = TABLE.delete_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            ReturnValues="ALL_OLD"
        )
        if 'Attributes' in res:
            return "Successfully deleted your location."
        else:
            return None
    except ClientError:
        raise

# partial update of an item's values
def update_location(author_id, location_name, new_coords):
    TABLE = get_table()
    try:
        res =  TABLE.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            UpdateExpression="set Coordinates = :newCoords",
            ExpressionAttributeValues={
                ":newCoords": encrypt(new_coords).decode()
            },
            ReturnValues="UPDATED_NEW",
            ConditionExpression="attribute_exists(Coordinates)"
        )
        if "Attributes" in res:
            return decrypt(res['Attributes']['Coordinates']).decode()
        else:
            return None
    except ClientError:
        raise

# seeds will be stored under a special location name
# avoids table sprawl
def set_seed(author_id, seed):
    TABLE = get_table()
    try:
        res = TABLE.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash("SEED")
            },
            UpdateExpression="set World_Seed = :seed",
            ExpressionAttributeValues={
                ":seed": encrypt(seed).decode()
            },
            ReturnValues="UPDATED_NEW",
        )
        if "Attributes" in res and "World_Seed" in res['Attributes']:
            return True, "Successfully set world seed."
        else:
            return False, "Failure setting world seed, try again later."
    except ClientError:
        raise
        
def get_seed(author_id):
    TABLE = get_table()
    try:
        res = TABLE.get_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash("SEED")
            }
        )
        if 'Item' in res and 'World_Seed' in res['Item']:
            encryptedSeed = res['Item']['World_Seed']
            return decrypt(encryptedSeed.encode()).decode()
        else: 
            return None
    except ClientError:
        raise
    
def list_locations(author_id):
    TABLE = get_table()
    try:
        response = TABLE.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("Author_ID").eq(str(author_id))
        )
        encrypted_locations = [item for item in response['Items']]
        unencrypted_locations = extract_decrypted_locations(encrypted_locations)
        # if the image URL exists, add it as a link for a specific location
        return "\n".join([ f"[{p['Location_Name']}]({p['Image_URL']}) — {p['Coordinates']}" if 'Image_URL' in p 
                          else f"{p['Location_Name']} — {p['Coordinates']}"
                        for p in unencrypted_locations
                    ])
    except ClientError:
        raise


async def save_image_url(author_id,location_name,message):
    TABLE = get_table()
    image_url = await storeImageInS3(message)
    try:
        res = TABLE.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            UpdateExpression="set Image_URL = :img_url",
            ExpressionAttributeValues={
                ":img_url": encrypt(image_url).decode()
            },
            ReturnValues="UPDATED_NEW",
        )
        if "Attributes" in res:
            return "Saved an image URL for your location."
        else:
            return None
    except Exception:
        raise
        

async def delete_image_url(author_id, location_name):
    TABLE = get_table()
    try:
        res = TABLE.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            UpdateExpression="REMOVE Image_URL",
            ReturnValues="ALL_OLD"
        )
        if "Attributes" in res:
            deleteURL = decrypt(res['Attributes']['Image_URL']).decode()
            await deleteImage(deleteURL)
    except Exception:
        raise
            