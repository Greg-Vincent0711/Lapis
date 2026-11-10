import os
import asyncio
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument

from src.lapis.helpers.utils import *
from src.lapis.helpers.docstrings import *
from src.lapis.helpers.exceptions import *
from src.lapis.helpers.embed import *
from src.lapis.helpers.paginator import *
from src.lapis.helpers.features import *
# The bot uses the same business logic layer as the website's API (db_lambda.py).
# Every function below validates its input, talks to DynamoDB/S3, and either returns
# plain decrypted data or raises an APIError with a message that's safe to show the user.
from src.lapis.api.middleware.errors import APIError, ValidationError
from src.lapis.api.services.db.db_services import (
    create_location,
    retrieve_location,
    retrieve_locations,
    create_location_update,
    delete_location_attempt,
    create_image,
    delete_image_url_attempt,
    set_seed,
    retrieve_seed,
)
from src.lapis.api.seed_impl import nearest_impl, spawn_near_impl

from dotenv import load_dotenv

'''
python3 -m src.lapis.lapis
'''

'''
TODO
All stuff remaining:
- Bot hosting + API setup with FastAPI
- Lapis Integration Tests for different bot use cases
    * Python <-> C code through subprocess.py (2-3 tests)
    * DynamoDB tests(maybe one end to end)
    * S3 tests
    * run unit/integration tests on git push
'''

load_dotenv()
TOKEN = os.getenv('TOKEN')
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# cooldown params
RATE = 1
PER: float = 5

# what users may type for the optional dimension in !save -> the value stored in the DB
LOCATION_TYPES = {
    "overworld": "Overworld",
    "nether": "Nether",
    "the end": "The End",
    "end": "The End",
}
# everything that can go wrong while storing an image that we want to explain to the user
IMAGE_ERRORS = (APIError, ValueError, InvalidImageFormatError, ImageDownloadError, S3UploadError)

@bot.event
async def on_ready():
    await bot.tree.sync()

@bot.event
async def on_guild_join(guild):
    # not every server has a system channel, or lets the bot post in it
    channel = guild.system_channel
    if channel is not None and channel.permissions_for(guild.me).send_messages:
        await channel.send(embed=makeEmbed("Hi!", "Send '!helpme' to get started."))

'''
 Start DB Functions
'''

# Copies the first attachment on the user's message into S3 and links it to the location
async def storeAttachment(ctx, locationName: str) -> str:
    if not ctx.message.attachments:
        raise ValidationError("Attach a .png or .jpg image to your message.")
    result = await create_image(str(ctx.author.id), locationName, ctx.message.attachments[0])
    return result["imageUrl"]

# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="save", help=saveDocString)
# the * lets the optional dimension contain a space without quotes: !save Base "1 2 3" the end
async def saveLocation(ctx, locationName: str, locationCoords: str, *, locationType: str = "Overworld"):
    try:
        # unknown types are passed through so the service can reject them with its own message
        locationType = LOCATION_TYPES.get(locationType.strip().lower(), locationType)
        create_location(str(ctx.author.id), locationName, locationType, locationCoords)
    except APIError as e:
        await ctx.send(embed=makeErrorEmbed("Error saving your location and coordinates.", e.message))
        return

    description = f"{format_coords(locationCoords)} ({locationType})"
    if ctx.message.attachments:
        # users can optionally save an image when first saving a location
        try:
            await storeAttachment(ctx, locationName)
        except IMAGE_ERRORS as e:
            description += f"\nYour image wasn't saved: {e}"
    await ctx.send(embed=makeEmbed(title=f"{locationName} has been saved.", description=description, authorName=ctx.author.display_name))


# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="get", help=getDocString)
async def getLocation(ctx, locationName: str):
    try:
        # always contains coordinates, may contain a type and an image URL
        location = retrieve_location(str(ctx.author.id), locationName)
    except APIError as e:
        if e.status_code == 404:
            await ctx.send(embed=makeErrorEmbed("No location with that name found.", "Call !list to see all locations."))
        else:
            await ctx.send(embed=makeErrorEmbed("Error getting coordinates for your location, try again later.", e.message))
        return

    description = location["Coordinates"]
    if location.get("Type"):
        description += f" ({location['Type']})"
    await ctx.send(embed=makeEmbed(title=f"Coordinates for {locationName}", description=description, authorName=ctx.author.display_name, url=location.get("Image_URL")))

        
# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="delete", help=deleteDocString)
async def deleteLocation(ctx, locationName: str):
    try:
        result = delete_location_attempt(str(ctx.author.id), locationName)
        await ctx.send(embed=makeEmbed(title="Success", description=result, authorName=ctx.author.display_name))
    except APIError as e:
        if e.status_code == 404:
            await ctx.send(embed=makeErrorEmbed(f"No matching location found for '{locationName}'.", "Call !list to see all locations you have created."))
        else:
            await ctx.send(embed=makeErrorEmbed(f"Error deleting {locationName}.", e.message))
            
# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="update", help=updateDocString)
async def updateLocation(ctx, locationName: str, newCoords: str):
    try:
        savedCoords = create_location_update(str(ctx.author.id), locationName, newCoords)
        await ctx.send(embed=makeEmbed(title=f"{locationName} updated successfully.", description=f"New coordinates: {savedCoords}", authorName=ctx.author.display_name))
    except APIError as e:
        await ctx.send(embed=makeErrorEmbed(f"Error updating {locationName}", e.message))

# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="list", help=listDocString)
async def list_locations_for_player(ctx):
    LOCATIONS_PER_PAGE = 3
    try:
        locations = retrieve_locations(str(ctx.author.id))
    except APIError as e:
        # the service raises a 404 when the user simply has nothing saved yet
        if e.status_code == 404:
            await ctx.send(embed=makeErrorEmbed("You have no locations to list."))
        else:
            await ctx.send(embed=makeErrorEmbed("Try this command again later.", e.message))
        return

    lines = [f"{loc['Location_Name']} — {loc['Coordinates']} ({loc['Type']})" for loc in locations]
    if len(lines) <= LOCATIONS_PER_PAGE:
        await ctx.send(embed=makeEmbed(title="Saved Locations", description="\n".join(lines), authorName=ctx.author.display_name))
    else:
        placesPerPage = paginate(lines, LOCATIONS_PER_PAGE, False)
        await ctx.send(embed=placesPerPage[0], view=Paginator(placesPerPage))
        

'''
Start S3 Functions
'''

# added tests
@commands.cooldown(RATE, PER * 2, commands.BucketType.user)
@bot.command(name="saveImg", help=saveImgDocString)
async def saveImage(ctx, location_name: str):
    if ctx.message.author.bot:
        await ctx.send(embed=makeErrorEmbed("Error", "Ignoring message from bot."))
        return
    try:
        imageUrl = await storeAttachment(ctx, location_name)
        await ctx.send(embed=makeEmbed(title="Success!", description=f"Saved an image for {location_name}.", authorName=ctx.author.display_name, url=imageUrl))
    except IMAGE_ERRORS as e:
        await ctx.send(embed=makeErrorEmbed("Error saving your image.", str(e)))

# added tests
@commands.cooldown(RATE, PER * 2, commands.BucketType.user)
@bot.command(name="deleteImg", help=deleteImgDocString)
async def deleteImage(ctx, locationName: str):
    try:
        await delete_image_url_attempt(str(ctx.author.id), locationName)
        await ctx.send(embed=makeEmbed("Successful image deletion.", f"For location {locationName}", ctx.author.display_name))
    except Exception as e:
        await ctx.send(embed=makeErrorEmbed("Error deleting image.", str(e)))

'''
seed functions
'''
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="ss", help=setSeedDocString)
async def setSeed(ctx, *, seed: str):
    try:
        result = set_seed(str(ctx.author.id), seed)
        await ctx.send(embed=makeEmbed(title=result["msg"], authorName=ctx.author.display_name))
    except APIError as e:
        await ctx.send(embed=makeErrorEmbed("Error setting your seed.", e.message))
        
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="gs", help=getSeedDocString)
async def getSeed(ctx):
    try:
        seed = retrieve_seed(str(ctx.author.id))
        await ctx.send(embed=makeEmbed("Retrieved Seed", f"{seed}"))
    except APIError as e:
        if e.status_code == 404:
            await ctx.send(embed=makeErrorEmbed("Error", "Could not find a seed for your user id. Set one with !ss."))
        else:
            await ctx.send(embed=makeErrorEmbed("Error", e.message))


'''
Start Nearest Fn
Streamlines the process of using the seed commands by adding some autocomplete features.
Each popup window only shows feature specific examples.
'''
MAX_SUGGESTIONS = 10

def suggest(options: list[str], current: str):
    current = current.lower()
    return [
        app_commands.Choice(name=option, value=option)
        for option in options
        if option.lower().startswith(current)
    ][:MAX_SUGGESTIONS]

async def biome_autocomplete(interaction: discord.Interaction, current: str):
    return suggest(BIOMES, current)

async def structure_autocomplete(interaction: discord.Interaction, current: str):
    return suggest(STRUCTURES, current)

# specifically for nearest(Structure/Biome)
async def feature_autocomplete(interaction: discord.Interaction, current: str):
    return suggest(ALL_FEATURES, current)

'''
Shared by both slash commands. seedTool is nearest_impl or spawn_near_impl - both run the
C executable, which can take a few seconds. So we tell Discord to wait (defer), run the
search on a worker thread so the bot stays responsive, then send the answer as a follow up.
'''
async def runSeedTool(interaction: discord.Interaction, title: str, seedTool, *args):
    await interaction.response.defer()
    try:
        result = await asyncio.to_thread(seedTool, str(interaction.user.id), *args)
    except APIError as e:
        hint = " Set one with !ss." if e.status_code == 404 else ""
        result = {"Error": f"{e.message}{hint}"}
    except ValueError as e:
        result = {"Error": str(e)}

    if "Error" in result:
        await interaction.followup.send(embed=makeErrorEmbed("Error", result["Error"]))
    else:
        await interaction.followup.send(embed=makeEmbed(title, result["result"], interaction.user.display_name))

@bot.tree.command(name="nearest", description=nearestDocString)
@app_commands.checks.cooldown(RATE, PER)
@app_commands.describe(
    feature="Structure or Biome name",
    x_coord="X coordinate",
    z_coord="Z coordinate",
    radius="Search radius"
)
@app_commands.autocomplete(feature=feature_autocomplete)
async def nearest(interaction: discord.Interaction, feature: str, x_coord: str, z_coord: str, radius: str):
    await runSeedTool(interaction, f"Nearest {feature}", nearest_impl, feature, x_coord, z_coord, radius)


# spawn_near numseeds biome structure range...
@bot.tree.command(name="spn", description=spawnNearDocString)
@app_commands.checks.cooldown(RATE, PER)
@app_commands.describe(
    numseeds="Requested seeds in range 1-10",
    biome="Biome you'd like to spawn in. Either this, or the structure param must be not be empty.",
    structure="Structure within a certain range of your spawn.",
    range="Distance from spawn the structure should be 3000 blocks or less."
)
@app_commands.autocomplete(biome=biome_autocomplete)
@app_commands.autocomplete(structure=structure_autocomplete)
async def spawn_near(interaction: discord.Interaction, numseeds: str, range: str, biome: Optional[str] = "None", structure: Optional[str] = "None"):
    await runSeedTool(interaction, "Found Seeds", spawn_near_impl, numseeds, range, biome, structure)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        embed = makeErrorEmbed("Wait before sending this command again.", f"Try again in {round(error.retry_after, 1)}s")
    else:
        embed = makeErrorEmbed("An error occured", str(error))
    # an interaction can only be answered once; after that, replies have to be follow ups
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed)
    else:
        await interaction.response.send_message(embed=embed)


@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="helpme", help=helpDocString)
async def help_command(ctx):
    CMDS_PER_PAGE = 3
    commands_list = [cmd for cmd in ctx.bot.commands if not cmd.hidden]
    pages = paginate(commands_list, CMDS_PER_PAGE, True)        
    await ctx.send(embed=pages[0], view=Paginator(pages))


@bot.command(name="logout", help="Logs the bot out of Discord. Bot owner only.", hidden=True)
@commands.is_owner()
async def logout(ctx):
    await ctx.send("Logging out...")
    await bot.close()
    
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send(embed=makeErrorEmbed("That command doesn't exist. Send `!helpme` for a list of all commands."))
    elif isinstance(error, MissingRequiredArgument):
        await ctx.send(embed=makeErrorEmbed("You're missing a required argument. Check `!helpme` for the proper format."))
    elif isinstance(error, BadArgument):
        await ctx.send(embed=makeErrorEmbed("Invalid argument type. Please check your input."))
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=makeErrorEmbed("Wait before sending this command again.", f"Try again in {round(error.retry_after, 1)}s"))
    else:
        # errors raised inside a command arrive wrapped; the original is the useful part
        original = getattr(error, "original", error)
        print(f"Unhandled error in !{ctx.command}: {type(original).__name__}: {original}")
        await ctx.send(embed=makeErrorEmbed("An error occured", str(original)))

if __name__ == "__main__":
    bot.run(TOKEN)
