'''
Business Logic Layer
Validates requests before accessing the repositories layer (DynamoDB, S3).

Both callers go through here:
    - the website, via the Lambda handlers in handler_methods/
    - the Discord bot, via direct imports in lapis.py

Every function either returns plain, already-decrypted data or raises an APIError
subclass (see middleware/errors.py). Callers never see raw DynamoDB responses.
'''
import logging
from src.lapis.helpers.utils import *
from src.lapis.helpers.exceptions import *
from src.lapis.api.middleware.errors import *
# imported as a module (not *) on purpose: some functions here share a name with the
# repository function they wrap (set_seed), and a star import would make them call themselves
from src.lapis.api.repositories import db
from src.lapis.api.repositories.s3_fns import storeImageInS3, deleteImage, deleteImageObject
from src.lapis.api.services.encryption.encryption import decrypt

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_LOCATIONS = 10

def create_location(author_id: str, location_name: str, location_type: str, coords: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests.")
    if not location_name or not coords:
        raise ValidationError("You must provide both a location name and coordinates")
    # these two validators return True, or a string explaining what's wrong
    nameCheck = isCorrectNameLength(location_name)
    if nameCheck is not True:
        raise ValidationError(nameCheck)
    coordCheck = isCorrectCoordFormat(coords)
    if coordCheck is not True:
        raise ValidationError(coordCheck)
    if not validType(location_type):
        raise ValidationError("Invalid location type provided. Use Overworld, Nether or The End.")

    current_count = db.get_location_count(author_id)
    if current_count >= MAX_LOCATIONS:
        raise LocationLimitExceededError(f"Max {MAX_LOCATIONS} locations allowed. Please delete one first.")
    # connect to data access layer. Coordinates are always stored as "x,y,z"
    db.save_location(author_id, location_name, location_type, format_coords(coords))
    return {
        "location_name": location_name,
        "remaining_locations": MAX_LOCATIONS - (current_count + 1)
    }

def set_seed(author_id: str, seed: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    if not seed:
        raise ValidationError("You must provide seed value.")
    seed = str(seed)
    if not validate_seed(seed):
        raise ValidationError(f"Invalid seed. Use 1-{MAX_SEED_LENGTH} printable characters.")
    # the C seed tools only understand numeric seeds, so text seeds are converted before storing
    res = db.set_seed(author_id, to_minecraft_seed(seed))
    if res.get("Attributes", {}).get("World_Seed"):
        return {"msg": "Successfully set world seed."}
    else:
        msg = "Failed to set world seed."
        logger.error(msg)
        raise DataAccessError(msg)

'''
image is anything with .url and .content_type (a Discord attachment, or the stand-in
the API handler builds). The image is copied into S3 and the S3 URL is saved on the location.
'''
async def create_image(author_id: str, location_name: str, image):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    if not location_name or not image:
        raise ValidationError("You must provide both a location name and an image.")
    # check the location exists before uploading, so a typo doesn't leave a stray file in S3
    existing = db.get_location(author_id, location_name)
    item = existing.get('Item', {})
    if 'Coordinates' not in item:
        raise InvalidLocationError(f"Location '{location_name}' not found.")

    image_url = await storeImageInS3(image, str(author_id))
    res = db.save_image_url(author_id, location_name, image_url)
    if "Attributes" in res:
        if item.get("Image_URL"):
            # the new image replaced an old one; remove the old file so it isn't orphaned in S3
            try:
                deleteImageObject(decrypt(item["Image_URL"]).decode())
            except Exception as e:
                logger.warning(f"Could not delete the replaced image: {e}")
        return {"msg": f"Saved image for location '{location_name}'.", "imageUrl": image_url}
    else:
        msg = f"Failed to save image URL for location '{location_name}'."
        logger.error("Failed to save an image URL")
        raise DataAccessError(msg)

def create_location_update(author_id: str, location_name: str, new_coords: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    if not location_name or not new_coords:
        raise ValidationError("You must provide both a location name and new coordinates for that location.")
    coordCheck = isCorrectCoordFormat(new_coords)
    if coordCheck is not True:
        raise ValidationError(coordCheck)

    res = db.update_location(author_id, location_name, format_coords(new_coords))
    if "Attributes" in res:
        return decrypt(res['Attributes']['Coordinates']).decode()
    else:
        msg = f"Location '{location_name}' not found or update failed."
        logger.error("Location update failed")
        raise DataAccessError(msg)

def retrieve_location(author_id: str, location_name: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    if not location_name:
        raise ValidationError("You must provide both a location name when attempting a get for a location.")

    res = db.get_location(author_id, location_name)
    item = res.get('Item', {})
    if 'Coordinates' not in item:
        raise InvalidLocationError(f"Location '{location_name}' not found.")

    result = {"Coordinates": decrypt(item['Coordinates']).decode()}
    if item.get("Location Type"):
        result["Type"] = decrypt(item["Location Type"]).decode()
    if item.get("Image_URL"):
        result["Image_URL"] = decrypt(item["Image_URL"]).decode()
    return result

def retrieve_locations(author_id: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    res = db.list_locations(author_id)
    unencrypted_locations = extract_decrypted_locations(res.get('Items', []))
    if unencrypted_locations:
        return unencrypted_locations
    else:
        raise NotFoundError("No locations exist for this user.")

def retrieve_seed(author_id: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    res = db.get_seed(author_id)
    if 'World_Seed' not in res.get('Item', {}):
        raise NotFoundError("World seed not found for this user.")
    return decrypt(res['Item']['World_Seed']).decode()


def delete_location_attempt(author_id: str, location_name: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    if not location_name:
        raise ValidationError("You must provide both a location name when attempting to delete a location.")

    res = db.delete_location(author_id, location_name)
    if "Attributes" in res:
        # a location's image goes with it. The row is already gone, so a failed
        # S3 cleanup is logged rather than reported as a failed delete
        image_url_encrypted = res["Attributes"].get("Image_URL")
        if image_url_encrypted:
            try:
                deleteImageObject(decrypt(image_url_encrypted).decode())
            except Exception as e:
                logger.error(f"Deleted a location but not its image: {type(e).__name__}")
        return f"Successfully deleted location '{location_name}'."
    else:
        msg = f"Location '{location_name}' not found."
        logger.info("Delete of a location that doesn't exist")
        raise NotFoundError(msg)

async def delete_image_url_attempt(author_id: str, location_name: str):
    if not author_id:
        raise UnauthorizedError("You must provide an author ID to make requests of any type.")
    if not location_name:
        raise ValidationError("You must provide both a location name when attempting to delete a location's image.")

    # raises NotFoundError if the location has no image
    res = db.delete_image_url(author_id, location_name)
    delete_url = decrypt(res['Attributes']['Image_URL']).decode()
    # two fold operation - delete the stored url AND the image data itself
    await deleteImage(delete_url)
    return f"Deleted image for location '{location_name}'."
