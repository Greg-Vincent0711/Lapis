import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from src.lapis.api.repositories.s3_fns import storeImageInS3, deleteImage
from src.lapis.api.services.encryption.encryption import encrypt, decrypt, generate_hash
from src.lapis.helpers.utils import extract_decrypted_locations
from src.lapis.api.middleware.errors import *
import os
import logging
# TODO - functions here need to be refactored to truly act as data access only
# There isn't a good separation of concerns here
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

def get_credentials(table, cognito_user_id: str) -> str:
    try:
        response = table.query(
            IndexName='cognito-index',
            KeyConditionExpression=Key('cognito_user_id').eq(cognito_user_id)
        )
        items = response.get("Items", [])
        return items

    except ClientError as e:
        raise DataAccessError(f"DynamoDB error: {e.response['Error']['Message']}") from e

def create_credentials(table, author_id: str, cognito_user_id: str):
    try:
        table.put_item(
            Item={
                'Author_ID': author_id,
                'Location': generate_hash("__PROFILE__"),
                'cognito_user_id': cognito_user_id
            }
        )
        return author_id
    except ClientError as e:
        raise DataAccessError(f"DynamoDB error: {e.response['Error']['Message']}") from e

    
# ---------------- POST / PUT METHODS ----------------
def save_location(author_id: str, location_name: str, location_type: str, coords: str) -> None:
    table = get_table()
    try:
        location_hash = generate_hash(location_name)
        table.put_item(
            Item={
                "Author_ID": str(author_id),
                "Location": location_hash,
                "Location_Name": encrypt(location_name).decode(),
                "Location Type": encrypt(location_type).decode(),
                "Coordinates": encrypt(coords).decode(),
            }
        )

    except ClientError as e:
        logger.error(f"Failed to save location: {e}")
        raise DataAccessError("Failed to save location") from e


# you could have errors bubble up - this returns {status code, msg}
# then, just pass that to the api caller through the handler
# so you may want to change return type of this

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
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError: {e}")
        raise DataAccessError("Failed to url for image") from e


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
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while setting seed: {e}")
        raise DataAccessError("ClientError while setting seed. Try again.") from e


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
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while updating location: {e}")
        raise DataAccessError("ClientError while updating location. Try again.")


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
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while fetching location: {e}")
        raise DataAccessError("ClientError while fetching location. Try again.")


def get_seed(author_id: str) -> str:
    table = get_table()
    try:
        res = table.get_item(
            Key={
                "Author_ID": str(author_id),
                "Location": "SEED"
            }
        )
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while fetching seed: {e}")
        raise DataAccessError("DynamoDB ClientError while fetching seed")


def list_locations(author_id: str) -> list[dict]:
    table = get_table()
    try:
        res = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("Author_ID").eq(str(author_id))
        )
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while listing locations: {e}")
        raise DataAccessError("DynamoDB ClientError while fetching your locations")


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
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while deleting location: {e}")
        raise DataAccessError(f"DynamoDB ClientError while deleting location: {e}")


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
        return res
    except ClientError as e:
        logger.error(f"DynamoDB ClientError while deleting image: {e}")
        raise DataAccessError(f"DynamoDB ClientError while deleting an image URL: {e}")



# def save_location(author_id: str, location_name: str, coords: str) -> str:
#     if get_location_count(author_id) >= 10:
#         return "Max locations saved for this user. 10 or less allowed."
#     else:
#         table = get_table()
#         location_hash = generate_hash(location_name)
#         res = table.put_item(
#             Item={
#                 "Author_ID": str(author_id),
#                 "Location": location_hash,
#                 "Location_Name": encrypt(location_name).decode(),
#                 "Coordinates": encrypt(coords).decode(),
#             }
#         )
        
#         status = res.get("ResponseMetadata", {}).get("HTTPStatusCode")
#         if status != 200:
#             msg = f"Failed to save location '{location_name}', status code {status}"
#             logger.error(msg)
#             return status, msg
                
#         new_count = get_location_count(author_id)
#         if new_count > 10:
#             logger.warning(f"Too many locations for user, deleting most recent.")
#             table.delete_item(
#                 Key={
#                     "Author_ID": str(author_id),
#                     "Location": location_hash
#                 }
#             )
#             return 202, "Request is accepted - Max locations saved however."
        
#         return 200, f"Successfully saved location '{location_name}'."
# repositories/location_repository.py

