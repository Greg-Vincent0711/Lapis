import boto3
from botocore.exceptions import ClientError
from src.lapis.backend.s3_fns import storeImageInS3, deleteImage
from src.lapis.encryption.encryption import encrypt, decrypt, generate_hash
from src.lapis.helpers.utils import extract_decrypted_locations
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_table():
    """
    Retrieve the DynamoDB table at runtime.
    """
    db_instance = boto3.resource('dynamodb', region_name=os.getenv("REGION_NAME"))
    table = db_instance.Table(os.getenv('TABLE_NAME'))
    return table


# ---------------- POST / PUT METHODS ----------------
def save_location(author_id: str, location_name: str, coords: str) -> str:
    table = get_table()
    res = table.put_item(
        Item={
            "Author_ID": str(author_id),
            "Location": generate_hash(location_name),
            "Location_Name": encrypt(location_name).decode(),
            "Coordinates": encrypt(coords).decode(),
        }
    )
    status = res.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status != 200:
        msg = f"Failed to save location '{location_name}', status code {status}"
        logger.error(msg)
        raise Exception(msg)
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
