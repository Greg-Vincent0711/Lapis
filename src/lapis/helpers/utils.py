import re
from src.lapis.encryption.encryption import decrypt
from src.lapis.helpers.features import ALL_FEATURES
import hashlib
import struct
import discord
from discord import app_commands

MAX_X_OR_Z = 30_000_000
MAX_Y = 320
MIN_Y = -64
MAX_SUGGESTIONS = 10

def isCorrectLength(name: str) -> str | bool:
    return True if len(name) <= 30 and len(name) >= 3 else "Invalid name length. Must between 3 and 30 characters."

# Checks for coord format and bounds of the coords sent
def isCorrectCoordFormat(coordinates: str) -> str | bool:
    match = re.fullmatch(r"\s*(-?\d+)\s*[,\s]+\s*(-?\d+)\s*[,\s]+\s*(-?\d+)\s*", coordinates)
    if not match:
        return "Incorrect format. Use double quotes around your numeric coordinates in the form 'X Y Z' or 'X,Y,Z'."
    try:
        x_coord, y_coord, z_coord = map(int, match.groups())
        if not (-MAX_X_OR_Z <= x_coord <= MAX_X_OR_Z):
            return f"X coordinate doesn't fit the bounds allowed within Minecraft...{-MAX_X_OR_Z} to {MAX_X_OR_Z}."
        if not (MIN_Y <= y_coord <= MAX_Y):
            return f"Y coordinate doesn't fit the bounds allowed within Minecraft...{MIN_Y} to {MAX_Y}."
        if not (-MAX_X_OR_Z <= z_coord <= MAX_X_OR_Z):
            return f"Z coordinate doesn't fit the bounds allowed within Minecraft...{-MAX_X_OR_Z} to {MAX_X_OR_Z}."
    except ValueError:
        return "Coordinates are not valid integers(can't be decimals like '10.5' for example)."
    return True

def extract_decrypted_locations(encryptedData):
    decryptedLocations = []
    for entry in encryptedData:
        try:
            decrypted_entry = {
                'Location_Name': decrypt(entry['Location_Name']).decode(),
                'Coordinates': decrypt(entry['Coordinates']).decode()
            }
            image_url_encrypted = entry.get("Image_URL")
            if image_url_encrypted:
                decrypted_entry["Image_URL"] = decrypt(image_url_encrypted.encode()).decode()
            decryptedLocations.append(decrypted_entry)
        except Exception as e:
            print(f"Error decrypting an item: {e}")
    return decryptedLocations

def format_coords(coord_string: str) -> str:
    individualCoords = [coord for coord in re.split(r'[,\s]+', coord_string.strip()) if coord]
    return ",".join(individualCoords)

def validate_seed(seed: str):
    printableCharacters = r'^[\w\s!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]+$'
    return 0 <= len(seed) <= 64 and re.match(printableCharacters, seed) != None

def to_minecraft_seed(seedValue: str):
    if re.match(r'\d+', seedValue) is not None:
        # numbers that can be passed in like 35 are already valid MC seeds
        return seedValue
    else:
        # If not a number, hash it using SHA-256 like Minecraft does
        hash_bytes = hashlib.sha256(seedValue.encode('utf-8')).digest()
        # Take the first 8 bytes and convert to signed 64-bit integer
        return str(struct.unpack('>q', hash_bytes[:8])[0])
    
# streamlines the process of using seedInfo commands
async def feature_autocomplete(interaction: discord.Interaction, word: str):
    word = word.lower()
    return [
        app_commands.Choice(name=feature, value=feature)
        for feature in ALL_FEATURES
        if feature.lower().startswith(word)
    ][:MAX_SUGGESTIONS]