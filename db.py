# db.py
import boto3
from botocore.exceptions import ClientError
from encryption import encrypt, decrypt, generate_hash
import os

dbInstance = boto3.resource('dynamodb')
TABLE = dbInstance.Table(os.getenv('TABLE_NAME'))


def save_location(author_id, location_name, coords):
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
    try:
        return TABLE.get_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            }
        )
        
    except ClientError as e:
        raise e

def delete_location(author_id, location_name):
    try:
        return TABLE.delete_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            ReturnValues="ALL_OLD"
        )
    except ClientError as e:
        raise e

def update_location(author_id, location_name, new_coords):
    try:
        return TABLE.update_item(
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
    except ClientError as e:
        raise e

def list_locations(author_id):
    try:
        return TABLE.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("Author_ID").eq(str(author_id))
        )
    except ClientError as e:
        raise e
