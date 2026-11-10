import re
from src.lapis.api.services.encryption.encryption import decrypt, generate_hash
# from src.lapis.helpers.features import *
from src.lapis.helpers.features import STRUCTURES, BIOMES

MAX_HORIZONTAL = 30_000_000
MAX_SEED_LENGTH = 64
MAX_VERTICAL = 320
MIN_VERTICAL = -64
MAX_SUGGESTIONS = 10

def isCorrectNameLength(name: str) -> str | bool:
    return True if len(name) <= 30 and len(name) >= 3 else "Invalid name length. Must between 3 and 30 characters."

# Checks for coord format and bounds of the coords sent
def isCorrectCoordFormat(coordinates: str) -> str | bool:
    match = re.fullmatch(r"\s*(-?\d+)\s*[,\s]+\s*(-?\d+)\s*[,\s]+\s*(-?\d+)\s*", coordinates)
    if not match:
        return "Incorrect format. Use double quotes around your numeric coordinates in the form 'X Y Z' or 'X,Y,Z'."
    try:
        x_coord, y_coord, z_coord = map(int, match.groups())
        if not (-MAX_HORIZONTAL <= x_coord <= MAX_HORIZONTAL):
            return f"X coordinate doesn't fit the bounds allowed within Minecraft...{-MAX_HORIZONTAL} to {MAX_HORIZONTAL}."
        if not (MIN_VERTICAL <= y_coord <= MAX_VERTICAL):
            return f"Y coordinate doesn't fit the bounds allowed within Minecraft...{MIN_VERTICAL} to {MAX_VERTICAL}."
        if not (-MAX_HORIZONTAL <= z_coord <= MAX_HORIZONTAL):
            return f"Z coordinate doesn't fit the bounds allowed within Minecraft...{-MAX_HORIZONTAL} to {MAX_HORIZONTAL}."
    except ValueError:
        return "Coordinates are not valid integers(can't be decimals like '10.5' for example)."
    return True

# hold onto this
# image_url_encrypted = entry.get("Image_URL")
                # if image_url_encrypted:
                #     decrypted_entry["Image_URL"] = decrypt(image_url_encrypted.encode()).decode()


# def extract_decrypted_locations(encryptedData):
#     decryptedLocations = []
#     for entry in encryptedData:
#         try:
#             # Exclude profile record
#             if entry.get("Location") != "__PROFILE__":
#                 decrypted_entry = {
#                     "Location_Name": decrypt(entry["Location_Name"]).decode(),
#                     "Coordinates": decrypt(entry["Coordinates"]).decode(),
#                     "Type": decrypt(entry["Location Type"]).decode()
#                 }
#                 decryptedLocations.append(decrypted_entry)
#         except Exception as e:
#             print("Failed entry:", entry)
#             print("Error:", e)
#     print("Outside loop")
#     print("Decrypted locations", decryptedLocations)
#     return decryptedLocations



# def extract_decrypted_locations(encryptedData):
#     decryptedLocations = []
#     for entry in encryptedData:
#         if entry.get("Location") == "__PROFILE__":
#             continue
#         try:
#             decryptedLocations.append({
#                 "Location_Name": decrypt(entry.get("Location_Name", b"")).decode(),
#                 "Coordinates": decrypt(entry.get("Coordinates", b"")).decode(),
#                 "Type": decrypt(entry.get("Location Type", b"")).decode()
#             })
#             print(decryptedLocations)
#         except Exception as e:
#             print(f"Failed to decrypt entry: {entry}. Error: {e}")
#             raise NotFoundError(f"Failed to decrypt entry: {entry}. Error: {e}")
    
#     return decryptedLocations
def extract_decrypted_locations(encryptedData):
    """
    Turns the raw rows for one user into a list of plain location dicts.
    Rows without a name and coordinates (the profile row, the seed row) aren't locations and are skipped.
    """
    decryptedLocations = []
    for entry in encryptedData:
        location_name_encrypted = entry.get("Location_Name")
        coordinates_encrypted = entry.get("Coordinates")
        if not location_name_encrypted or not coordinates_encrypted:
            continue
        try:
            # locations saved before types existed have no "Location Type"
            type_encrypted = entry.get("Location Type")
            decryptedLocations.append({
                "Location_Name": decrypt(location_name_encrypted).decode(),
                "Coordinates": decrypt(coordinates_encrypted).decode(),
                "Type": decrypt(type_encrypted).decode() if type_encrypted else "Overworld"
            })
            image_encrypted = entry.get("Image_URL")
            if image_encrypted:
                decryptedLocations[-1]["Image_URL"] = decrypt(image_encrypted).decode()
        except Exception as e:
            # one unreadable row shouldn't hide the rest of the user's locations
            print(f"Skipping a location that could not be decrypted: {type(e).__name__}: {e}")
            continue
    return decryptedLocations


'''
normalizes coordinates: 
    format_coords(" 12  ,  34,56 ") -> "12,34,56"
    format_coords("12 34  56") -> "12,34,56"
'''
def format_coords(coord_string: str) -> str:
    individualCoords = [coord for coord in re.split(r'[,\s]+', coord_string.strip()) if coord]
    return ",".join(individualCoords)

def validType(type: str) -> bool:
    return type in ["Overworld", "Nether", "The End"]

# seeds must only contain printable characters
def validate_seed(seed: str):
    printableCharacters = r'^[\w\s!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]+$'
    return 1 <= len(seed.replace(" ", "")) <= MAX_SEED_LENGTH and re.match(printableCharacters, seed) is not None

INT64_MIN, INT64_MAX = -2**63, 2**63 - 1

def java_string_hash(text: str) -> int:
    """
    Java's String.hashCode(): h = 31*h + c over the UTF-16 code units, kept to a signed 32-bit int.
    "hello" -> 99162322, the same number Java gives.
    """
    utf16 = text.encode("utf-16-be")
    h = 0
    for i in range(0, len(utf16), 2):
        h = (31 * h + int.from_bytes(utf16[i:i + 2], "big")) & 0xFFFFFFFF
    return h - 2**32 if h >= 2**31 else h

def to_minecraft_seed(seedValue: str) -> str:
    """
    Turns what a player typed into the number Minecraft Java Edition uses for that world:
      "12345"   -> "12345"  (a whole number that fits in a 64-bit long is used as-is)
      "glacier" -> its Java hashCode, as Minecraft does for any seed that isn't such a number
    Running it on its own output changes nothing, so it's safe to apply when reading as well as saving.
    """
    seedValue = seedValue.strip()
    if re.fullmatch(r'-?\d+', seedValue) is not None and INT64_MIN <= int(seedValue) <= INT64_MAX:
        return str(int(seedValue))
    # numbers too big for a long fail Java's Long.parseLong too, so Minecraft hashes those as text
    return str(java_string_hash(seedValue))

# inputHandler.c looks features up by the exact cubiomes enum name:
#   structures keep their capitals -> "Desert_Pyramid"
#   biomes are lowercase           -> "frozen_ocean"
# users may type any casing, with spaces, dashes or underscores
def _normalize_feature(feature: str) -> str:
    return re.sub(r'[\s_\-]+', ' ', feature.strip().lower())

_STRUCTURE_NAMES = {_normalize_feature(name): name.replace(" ", "_") for name in STRUCTURES}
UNUSED_FEATURE = "None"

def is_structure(feature: str) -> bool:
    return bool(feature) and _normalize_feature(feature) in _STRUCTURE_NAMES

# feature is either a structure or biome
def format_feature(feature: str | None) -> str:
    if not feature or _normalize_feature(feature) == "none":
        # spawnNear.c treats the literal "None" as "this filter is unused"
        return UNUSED_FEATURE
    normalized = _normalize_feature(feature)
    if normalized in _STRUCTURE_NAMES:
        return _STRUCTURE_NAMES[normalized]
    return normalized.replace(" ", "_")


'''
Streamlines the process of using seedInfo commands by adding some autocomplete features

Note to remember for the future:
A more efficient solution is to have one function that switches lists
based on some parameter value so we aren't repeating logic. But the process to implement
that isn't very simple since you'd have to infer the value from the interaction object
that's passed. It may create more work than needed. So for now, repeat auto_completes is ok.
'''

# first two are for spawn near. Each popup window only shows feature specific examples.
# async def biome_autocomplete(interaction: discord.Interaction, current: str):
#     current = current.lower()
#     return [
#         app_commands.Choice(name=feature, value=feature)
#         for feature in BIOMES
#         if feature.lower().startswith(current)
#     ][:MAX_SUGGESTIONS]
    
# async def structure_autocomplete(interaction: discord.Interaction, current: str):
#     current = current.lower()
#     return [
#         app_commands.Choice(name=feature, value=feature)
#         for feature in STRUCTURES
#         if feature.lower().startswith(current)
#     ][:MAX_SUGGESTIONS]

# # specifically for nearest(Structure/Biome)
# async def feature_autocomplete(interaction: discord.Interaction, current: str):
#     current = current.lower()
#     return [
#         app_commands.Choice(name=feature, value=feature)
#         for feature in ALL_FEATURES
#         if feature.lower().startswith(current)
#     ][:MAX_SUGGESTIONS]
