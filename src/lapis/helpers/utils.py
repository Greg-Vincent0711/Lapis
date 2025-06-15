import re
from src.lapis.encryption.encryption import decrypt
from src.lapis.helpers.features import *
import hashlib
import struct
import discord
from discord import app_commands

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

'''
normalizes coordinates: 
    format_coords(" 12  ,  34,56 ") -> "12,34,56"
    format_coords("12 34  56") -> "12,34,56"
'''
def format_coords(coord_string: str) -> str:
    individualCoords = [coord for coord in re.split(r'[,\s]+', coord_string.strip()) if coord]
    return ",".join(individualCoords)

# seeds must only contain printable characters
def validate_seed(seed: str):
    printableCharacters = r'^[\w\s!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]+$'
    return 1 <= len(seed.replace(" ", "")) <= MAX_SEED_LENGTH and re.match(printableCharacters, seed) is not None

def to_minecraft_seed(seedValue: str):
    if re.match(r'\d+', seedValue) is not None:
        # numbers that can be passed in like 35 are already valid MC seeds
        return seedValue
    else:
        # If not a number, hash it using SHA-256 like Minecraft does
        hash_bytes = hashlib.sha256(seedValue.encode('utf-8')).digest()
        # Take the first 8 bytes and convert to signed 64-bit integer
        return str(struct.unpack('>q', hash_bytes[:8])[0])

# feature is either a structure or biome
def format_feature(feature: str):
    if feature in STRUCTURES:
        feature = feature.replace(" ", "-")
    elif feature in BIOMES:
        feature = feature.lower().replace(" ", "-")
    return feature
'''
Streamlines the process of using seedInfo commands by adding some autocomplete features

Note to remember for the future:
A more efficient solution is to have one function that switches lists
based on some parameter value so we aren't repeating logic. But the process to implement
that isn't very simple since you'd have to infer the value from the interaction object
that's passed. It may create more work than needed. So for now, repeat auto_completes is ok.
'''

# first two are for spawn near. Each popup window only shows feature specific examples.
async def biome_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    return [
        app_commands.Choice(name=feature, value=feature)
        for feature in BIOMES
        if feature.lower().startswith(current)
    ][:MAX_SUGGESTIONS]
    
async def structure_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    return [
        app_commands.Choice(name=feature, value=feature)
        for feature in STRUCTURES
        if feature.lower().startswith(current)
    ][:MAX_SUGGESTIONS]

# specifically for nearest(Structure/Biome)
async def feature_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    return [
        app_commands.Choice(name=feature, value=feature)
        for feature in ALL_FEATURES
        if feature.lower().startswith(current)
    ][:MAX_SUGGESTIONS]
