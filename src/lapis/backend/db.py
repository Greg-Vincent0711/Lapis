import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from src.lapis.backend.s3_fns import storeImageInS3, deleteImage
from src.lapis.encryption.encryption import encrypt, decrypt, generate_hash
from src.lapis.helpers.utils import extract_decrypted_locations
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
MAX = 10

def get_table():
    """
    Retrieve the DynamoDB table at runtime.
    """
    db_instance = boto3.resource('dynamodb', region_name=os.getenv("REGION_NAME"))
    table = db_instance.Table(os.getenv('TABLE_NAME'))
    return table

def get_location_count(author_id: str):
    # Get table
    table = get_table()
    # Query for all user locations for an author_id
    response = table.query(
        KeyConditionExpression=Key('Author_ID').eq(author_id),
        Select='COUNT'
    )    
    return response['Count']

def get_credentials(cognito_user_id: str):
    try:
        table = get_table()
        response = table.query(
            IndexName='cognito-index',
            KeyConditionExpression=Key('cognito_user_id').eq(cognito_user_id)
        )
        
        if response['Items']:
            return response['Items'][0]['Author_ID']
        return None
        
    except ClientError as e:
        print(f"DynamoDB error in get_credentials: {e.response['Error']['Message']}")
        raise Exception("Failed to retrieve credentials from database")
    except Exception as e:
        print(f"Unexpected error in get_credentials: {str(e)}")
        raise Exception("Failed to retrieve credentials")


def save_credentials(cognito_user_id: str, author_id: str):
    try:
        table = get_table()
        existing_author_id = get_credentials(cognito_user_id)
        
        if existing_author_id is None:
            table.put_item(
                Item={
                    'Author_ID': author_id,
                    'cognito_user_id': cognito_user_id
                }
            )
            return 200, "Credentials saved successfully."
        else:
            if existing_author_id != author_id:
                table.update_item(
                    Key={'Author_ID': existing_author_id},
                    UpdateExpression='SET cognito_user_id = :cid',
                    ExpressionAttributeValues={':cid': cognito_user_id}
                )
                return 200, "Credentials updated successfully."
            return 200, "Credentials already exist."
            
    except ClientError as e:
        print(f"DynamoDB error in save_credentials: {e.response['Error']['Message']}")
        return 500, "Failed to save credentials to database"
    except Exception as e:
        print(f"Unexpected error in save_credentials: {str(e)}")
        return 500, "Failed to save credentials"
    
# ---------------- POST / PUT METHODS ----------------
def save_location(author_id: str, location_name: str, coords: str) -> str:
    if get_location_count(author_id) >= 10:
        return "Max locations saved for this user. 10 or less allowed."
    else:
        table = get_table()
        location_hash = generate_hash(location_name)
        res = table.put_item(
            Item={
                "Author_ID": str(author_id),
                "Location": location_hash,
                "Location_Name": encrypt(location_name).decode(),
                "Coordinates": encrypt(coords).decode(),
            }
        )
        
        status = res.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status != 200:
            msg = f"Failed to save location '{location_name}', status code {status}"
            logger.error(msg)
            raise Exception(msg)
                
        new_count = get_location_count(author_id)
        if new_count > 10:
            logger.warning(f"Too many locations for user, deleting most recent.")
            table.delete_item(
                Key={
                    "Author_ID": str(author_id),
                    "Location": location_hash
                }
            )
            return "Maximum locations saved. Please try again."
        
        return f"Successfully saved location '{location_name}'."
    
async def save_image_url(author_id: str, location_name: str, message) -> str:
    table = get_table()
    image_url = await storeImageInS3(message)

    try:
        res = table.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            UpdateExpression="SET Image_URL = :img_url",
            ExpressionAttributeValues={
                ":img_url": encrypt(image_url).decode()
            },
            ReturnValues="UPDATED_NEW",
        )
        if "Attributes" in res:
            return f"Saved image URL for location '{location_name}'."
        else:
            msg = f"Failed to update image URL for location '{location_name}'."
            logger.error(msg)
            raise Exception(msg)
    except ClientError as e:
        logger.error(f"DynamoDB ClientError: {e}")
        raise


def set_seed(author_id: str, seed: str) -> tuple[bool, str]:
    table = get_table()
    try:
        res = table.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": "SEED"
            },
            UpdateExpression="SET World_Seed = :seed",
            ExpressionAttributeValues={
                ":seed": encrypt(seed).decode()
            },
            ReturnValues="UPDATED_NEW",
        )
        if res.get("Attributes", {}).get("World_Seed"):
            return True, "Successfully set world seed."
        else:
            msg = "Failed to set world seed."
            logger.error(msg)
            return False, msg
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while setting seed: {e}")
        raise


def update_location(author_id: str, location_name: str, new_coords: str) -> str:
    table = get_table()
    try:
        res = table.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            UpdateExpression="SET Coordinates = :newCoords",
            ExpressionAttributeValues={
                ":newCoords": encrypt(new_coords).decode()
            },
            ReturnValues="UPDATED_NEW",
            ConditionExpression="attribute_exists(Coordinates)"
        )
        if "Attributes" in res:
            return decrypt(res['Attributes']['Coordinates']).decode()
        else:
            msg = f"Location '{location_name}' not found or update failed."
            logger.error(msg)
            raise Exception(msg)
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while updating location: {e}")
        raise


# ---------------- GET METHODS ----------------
def get_location(author_id: str, location_name: str) -> dict:
    table = get_table()
    try:
        res = table.get_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            }
        )
        if 'Item' not in res:
            raise Exception(f"Location '{location_name}' not found.")

        item = res['Item']
        decrypted_coords = decrypt(item['Coordinates'].encode()).decode()
        result = {"Coordinates": decrypted_coords}

        if item.get("Image_URL"):
            result["Image_URL"] = decrypt(item["Image_URL"].encode()).decode()

        return result
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while fetching location: {e}")
        raise


def get_seed(author_id: str) -> str:
    table = get_table()
    try:
        res = table.get_item(
            Key={
                "Author_ID": str(author_id),
                "Location": "SEED"
            }
        )
        if 'Item' not in res or 'World_Seed' not in res['Item']:
            raise Exception("World seed not found.")

        return decrypt(res['Item']['World_Seed'].encode()).decode()
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while fetching seed: {e}")
        raise


def list_locations(author_id: str) -> list[dict]:
    table = get_table()
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("Author_ID").eq(str(author_id))
        )
        encrypted_locations = response.get('Items', [])
        unencrypted_locations = extract_decrypted_locations(encrypted_locations)
        return unencrypted_locations
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while listing locations: {e}")
        raise


# ---------------- DELETE METHODS ----------------
def delete_location(author_id: str, location_name: str) -> str:
    table = get_table()
    try:
        res = table.delete_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            ReturnValues="ALL_OLD"
        )
        if "Attributes" in res:
            return f"Successfully deleted location '{location_name}'."
        else:
            msg = f"Location '{location_name}' not found."
            logger.error(msg)
            raise Exception(msg)
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while deleting location: {e}")
        raise


async def delete_image_url(author_id: str, location_name: str) -> str:
    table = get_table()
    try:
        res = table.update_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            UpdateExpression="REMOVE Image_URL",
            ReturnValues="ALL_OLD"
        )
        if "Attributes" in res and "Image_URL" in res["Attributes"]:
            delete_url = decrypt(res['Attributes']['Image_URL']).decode()
            await deleteImage(delete_url)
            return f"Deleted image URL for location '{location_name}'."
        else:
            msg = f"No image found for location '{location_name}'."
            logger.error(msg)
            raise Exception(msg)
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while deleting image: {e}")
        raise
