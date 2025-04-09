# db.py
import boto3
from botocore.exceptions import ClientError
from encryption import encrypt, decrypt, generate_hash
from utils import extract_decrypted_locations, format_coords
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
        res = TABLE.get_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            }
        )
        if 'Item' in res:
            encryptedCoordinates = res['Item']['Coordinates']
            retrieved_coordinates = format_coords(decrypt(encryptedCoordinates.encode()).decode())
            return retrieved_coordinates
        else: 
            return None
    
    except ClientError as e:
        raise e

def delete_location(author_id, location_name):
    try:
        res = TABLE.delete_item(
            Key={
                "Author_ID": str(author_id),
                "Location": generate_hash(location_name)
            },
            ReturnValues="ALL_OLD"
        )
        if 'Attributes' in res:
            return format_coords(decrypt(res["Attributes"]["Coordinates"]).decode())
        else:
            return None
    except ClientError as e:
        raise e

def update_location(author_id, location_name, new_coords):
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
            return format_coords(decrypt(res['Attributes']['Coordinates']).decode())
        else:
            return None
            
        
    except ClientError as e:
        raise e

def list_locations(author_id):
    try:
        response = TABLE.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("Author_ID").eq(str(author_id))
        )
        encrypted_locations = [item for item in response['Items']]
        unencrypted_locations = extract_decrypted_locations(encrypted_locations)
        return "\n".join([f"{p['Location_Name']} — {format_coords(p['Coordinates'])}" for p in unencrypted_locations])
    except ClientError as e:
        raise e
