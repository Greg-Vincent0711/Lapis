'''
Business Logic Layer
Validates http requests before accessing repositories layer(db)

Really, just check for a lot of different error cases
then if we pass them all, call the external service
'''
from src.lapis.helpers.utils import *
from api.middleware.errors import *
from api.repositories.db import *

def create_location(author_id: str, location_name: str, coords: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests.")
    elif not location_name or not coords:
        raise ValidationError("You must provide both a location name and coordinates")
    elif not isCorrectNameLength(location_name):
        raise InvalidLocationError(f"The location name provided: {location_name} is invalid.")
    elif not isCorrectCoordFormat(coords):
        raise InvalidLocationError(f"Invalid coordinates provided: {coords}.")
    elif get_location_count(author_id) >= 10:
        raise LocationLimitExceededError("Max 10 locations allowed. Please delete one first.")
    else:
        remaining = 10 - (get_location_count(author_id) + 1)
        # connect to data access layer
        save_location(author_id, location_name, coords)            
        return {
            "location_name": location_name,
            "remaining_locations": remaining
        }

def create_seed(author_id: str, seed: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    elif not seed:
        raise ValidationError("You must provide seed value.")
    else:
        res = set_seed(author_id, seed)
        if res.get("Attributes", {}).get("World_Seed"):
            return {"msg": "Successfully set world seed."}
        else:
            msg = "Failed to set world seed."
            logger.error(msg)
            raise DataAccessError(msg)
        
def create_image(author_id: str, location_name: str, message):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    elif not location_name or not message:
        raise ValidationError("You must provide both a location name and a message object containing the image data.")
    else:
        res = save_image_url(author_id, location_name, message)
        if "Attributes" in res:
            return {"msg" :f"Saved image URL for location '{location_name}'."}
        else:
            msg = f"Failed to save image URL for location '{location_name}'."
            logger.error(msg)
            raise DataAccessError(msg)

def create_location_update(author_id: str, location_name: str, new_coords: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    elif not location_name or not new_coords:
        raise ValidationError("You must provide both a location name and new coordinates for that location.")
    else:
        res = update_location(author_id, location_name, new_coords)
        if "Attributes" in res:
            return decrypt(res['Attributes']['Coordinates']).decode()
        else:
            msg = f"Location '{location_name}' not found or update failed."
            logger.error(msg)
            raise DataAccessError(msg)

def retrieve_location(author_id: str, location_name: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    elif not location_name:
        raise ValidationError("You must provide both a location name when attempting a get for a location.")
    else:
        res = get_location(author_id, location_name)
        if 'Item' not in res:
            raise InvalidLocationError(f"Location '{location_name}' not found.")
        
        item = res['Item']
        decrypted_coords = decrypt(item['Coordinates'].encode()).decode()
        result = {"Coordinates": decrypted_coords}

        if item.get("Image_URL"):
            result["Image_URL"] = decrypt(item["Image_URL"].encode()).decode()
        return result

def retrieve_locations(author_id: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    res = list_locations(author_id)
    encrypted_locations = res.get('Items', [])
    unencrypted_locations = extract_decrypted_locations(encrypted_locations)
    if len(encrypted_locations) >= 1:
        return unencrypted_locations
    else:
        raise NotFoundError("No locations exist for this user.")

def retrieve_seed(author_id: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    else:
        res = get_seed(author_id)
        if 'Item' not in res or 'World_Seed' not in res['Item']:
            raise NotFoundError("World seed not found for this user.")
        return decrypt(res['Item']['World_Seed'].encode()).decode()

            
def delete_location_attempt(author_id: str, location_name: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    elif not location_name:
        raise ValidationError("You must provide both a location name when attempting to delete a location.")
    else:
        res = delete_location(author_id, location_name)
        if "Attributes" in res:
            return f"Successfully deleted location '{location_name}'."
        else:
            msg = f"Location '{location_name}' not found."
            logger.error(msg)
            raise NotFoundError(msg)
        
async def delete_image_url_attempt(author_id: str, location_name: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    elif not location_name:
        raise ValidationError("You must provide both a location name when attempting to delete a location's image.")
    else:
        res = delete_image_url(author_id, location_name)
        if "Attributes" in res and "Image_URL" in res["Attributes"]:
            delete_url = decrypt(res['Attributes']['Image_URL']).decode()
            # two fold operation - delete the generated url AND the image data itself
            await deleteImage(delete_url)
            return f"Deleted image URL for location '{location_name}'."
        else:
            msg = f"No image found for location '{location_name}'."
            logger.error(msg)
            raise NotFoundError(msg)