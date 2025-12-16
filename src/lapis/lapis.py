import os
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
from src.lapis.api.repositories.db import *
# from src.lapis.backend.cache import *
from src.lapis.api.seed_impl import *
from src.lapis.helpers.features import *

from dotenv import load_dotenv
from botocore.exceptions import ClientError

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

@bot.event
async def on_ready():
    await bot.tree.sync()

@bot.event
async def on_guild_join(ctx):
    await ctx.send(embed=makeEmbed("Hi!", "Send '!helpme' to get started."))

'''
 Start DB Functions
'''

# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="save", help=saveDocString)
async def saveLocation(ctx, locationName: str, locationCoords: str): 
    nameCheck = isCorrectNameLength(locationName)
    coordCheck = isCorrectCoordFormat(locationCoords)
    # both of these fns return error messages if not True
    if nameCheck is not True:
        await ctx.send(embed=makeErrorEmbed("Error", f"{nameCheck}"))
    
    elif coordCheck is not True:
        await ctx.send(embed=makeErrorEmbed("Error", f"{coordCheck}"))
    else:
        try:
            formattedCoords = format_coords(locationCoords)
            save_location(ctx.author.id, locationName, formattedCoords)
            if ctx.message.attachments:
                # users can optionally save an image when first saving a location
                await saveImage(ctx, locationName)
            await ctx.send(embed=makeEmbed(title=f"{locationName} has been saved.", description=formattedCoords, authorName=ctx.author.display_name))
        except Exception as e:
            await ctx.send(embed=makeErrorEmbed("Error saving your location and coordinates.", {e}))


# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="get", help=getDocString)
async def getLocation(ctx, locationName: str):
    nameCheck = isCorrectNameLength(locationName)
    if nameCheck is not True:
        await ctx.send(embed=makeErrorEmbed("Error", f"{nameCheck}"))
    else:
        try:
            # always contains coordinates, may contain an image URL 
            retrieved_data = get_location(ctx.author.id, locationName)
            if retrieved_data is not None:
                if len(retrieved_data) > 1 and retrieved_data[1] is not None:
                    await ctx.send(embed=makeEmbed(title=f"Coordinates for {locationName}", description=f"{retrieved_data[0]}", authorName=ctx.author.display_name, url=retrieved_data[1]))
                else:
                    await ctx.send(embed=makeEmbed(title=f"Coordinates for {locationName}", description=f"{retrieved_data[0]}", authorName=ctx.author.display_name))
            else:
                await ctx.send(embed=makeErrorEmbed(f"No location with that name found.", f"Call !list to see all locations."))
        except ClientError as e:
            await ctx.send(embed=makeErrorEmbed(f'Error getting coordinates for your location, try again later.', {e}))

        
# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="delete", help=deleteDocString)
async def deleteLocation(ctx, locationName: str):
    nameCheck = isCorrectNameLength(locationName)
    if nameCheck is not True:   
        await ctx.send(f"{nameCheck}")
    else:
        try:
            result = await delete_location(ctx.author.id, locationName)
            if result != None:
                await ctx.send(embed=makeEmbed(title="Success", description=result, authorName=ctx.author.display_name, ))
            else:
                await ctx.send(embed=makeErrorEmbed(f"No matching location found for '{locationName}'. Call !list to see all locations you have created."))
        except ClientError as e:
            error_message = e.response["Error"]["Message"]
            await ctx.send(makeErrorEmbed(f'Error deleting {locationName}.', error_message))
            
# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="update", help=updateDocString)
async def updateLocation(ctx, locationName, newCoords):
    nameCheck = isCorrectNameLength(locationName)
    coordCheck = isCorrectCoordFormat(newCoords)
    if nameCheck is not True:
        await ctx.send(f"{nameCheck}")
    elif coordCheck is not True:
        await ctx.send(f"{coordCheck}")
    else:
        try:
            response = update_location(ctx.author.id, locationName, format_coords(newCoords))
            if response != None:
                await ctx.send(embed=makeEmbed(title=f"{locationName} updated successfully.", description=f"New coordinates: {response}", authorName=ctx.author.display_name))
            else:
                await ctx.send(embed=makeErrorEmbed(f"Error updating {locationName}"))
        except ClientError as e:
            error_message = e.response["Error"]["Message"]
            await ctx.send(embed=makeErrorEmbed(f'Error updating {locationName}', error_message))

# added tests
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="list", help=listDocString)
async def list_locations_for_player(ctx):
    LOCATIONS_PER_PAGE = 3
    try:
        player_locations = list_locations(ctx.author.id)
        if 1 <= len(player_locations) <= LOCATIONS_PER_PAGE:
            await ctx.send(embed=makeEmbed(description=player_locations, authorName=ctx.author.display_name))
        elif len(player_locations) > LOCATIONS_PER_PAGE:
            placesPerPage = paginate(player_locations.split("\n"), LOCATIONS_PER_PAGE, False)
            await ctx.send(embed=placesPerPage[0], view=Paginator(placesPerPage))
        else:
            await ctx.send(embed=makeErrorEmbed("You have no locations to list."))
    except ClientError as e:
        await ctx.send(embed=makeErrorEmbed("Try this command again later.", {e}))
        

'''
Start S3 Functions
'''

# added tests
@commands.cooldown(RATE, PER * 2, commands.BucketType.user)
@bot.command(name="saveImg", help=saveImgDocString)
async def saveImage(ctx, location_name):
    nameCheck = isCorrectNameLength(location_name)
    if nameCheck is not True:
        await ctx.send(embed=makeErrorEmbed("Error", nameCheck))
    else: 
        message = ctx.message
        if message.author.bot:
            await ctx.send(embed=makeErrorEmbed("Error","Ignoring message from bot."))  
        else:     
            try:
                author_id = ctx.author.id
                result = await save_image_url(author_id, location_name, message)
                if result is not None:
                    await ctx.send(embed=makeEmbed(title="Success!", description=result))
                else:
                    await ctx.send(embed=makeErrorEmbed("Image not saved", "Failed to update the database. Try again later."))
            except (ValueError, InvalidImageFormatError, ImageDownloadError, S3UploadError) as e:
                await ctx.send(embed=makeErrorEmbed("Error saving your image.", str(e)))

# added tests
@commands.cooldown(RATE, PER * 2, commands.BucketType.user)
@bot.command(name="deleteImg", help=deleteImgDocString)
async def deleteImage(ctx, locationName):
    nameCheck = isCorrectNameLength(locationName)
    if nameCheck is not True:
        await ctx.send(embed=makeErrorEmbed("Error", nameCheck))
    else:
        try:
            await delete_image_url(ctx.author.id, locationName)
            await ctx.send(embed=makeEmbed("Successful image deletion.", f"For location {locationName}", ctx.author.display_name))
        except Exception as e:
            await ctx.send(embed=makeErrorEmbed("Error deleting image.", str(e)))

'''
seed functions
'''
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="ss", help=setSeedDocString)
async def setSeed(ctx, seed: str):
    if validate_seed(seed):
        setSeedAttempt = set_seed(ctx.author.id, to_minecraft_seed(seed))
        # res[1] contains a success/error message
        await ctx.send(embed=makeEmbed(title=setSeedAttempt[1]))
        
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="gs", help=getSeedDocString)
async def getSeed(ctx):
    seed = get_seed(ctx.author.id)
    if seed is not None:
         await ctx.send(embed=makeEmbed("Retrieved Seed", f"{seed}"))
    else:
        await ctx.send(makeErrorEmbed("Error", "Could not find a seed for your user id."))


'''
Start Nearest Fn
'''

@bot.tree.command(name="nearest", description=nearestDocString)
@commands.cooldown(RATE, PER, commands.BucketType.user)
@app_commands.describe(
    feature="Structure or Biome name",
    x_coord="X coordinate",
    z_coord="Z coordinate",
    radius="Search radius"
)
@app_commands.autocomplete(feature=feature_autocomplete)
async def nearest(interaction: discord.Interaction, feature: str, x_coord: str, z_coord: str, radius: str):
    # added tests to nearest_impl
    await nearest_impl(interaction, feature, x_coord, z_coord, radius)


# spawn_near numseeds biome structure range...
@bot.tree.command(name="spn", description=spawnNearDocString)
@commands.cooldown(RATE, PER, commands.BucketType.user)
@app_commands.describe(
    numseeds="Requested seeds in range 1-10",
    biome="Biome you'd like to spawn in. Either this, or the structure param must be not be empty.",
    structure="Structure within a certain range of your spawn.",
    range="Distance from spawn the structure should be 3000 blocks or less."
)
@app_commands.autocomplete(biome=biome_autocomplete)
@app_commands.autocomplete(structure=structure_autocomplete)
async def spawn_near(interaction: discord.Interaction, numseeds: str, range: str, biome: Optional[str] = "None", structure: Optional[str] = "None"):
    # added tests
    await spawn_near_impl(interaction, numseeds, range, biome, structure)



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
        await ctx.send(embed=makeErrorEmbed("An error occured", error))

if __name__ == "__main__":
    bot.run(TOKEN)

