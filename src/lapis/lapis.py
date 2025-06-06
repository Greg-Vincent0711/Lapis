import os
import discord
from discord import Embed, app_commands
from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument

from src.lapis.helpers.utils import *
from src.lapis.helpers.docstrings import *
from src.lapis.helpers.exceptions import *
from src.lapis.helpers.embed import *
from src.lapis.helpers.paginator import *

from src.lapis.backend.db import *
from src.lapis.backend.cache import *
from src.lapis.backend.subprocess import connectToInputHandler
from src.lapis.helpers.features import *

from dotenv import load_dotenv
from botocore.exceptions import ClientError



'''
TODO
Finish caching stuff - invalidation
Implement spawn_near frontend
api stuff/hosting
make it so that the error json from the inputHandler.c code works properly
Tests
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
    print(f'{bot.user.name} has connected to Discord!')

'''
 Start DB Functions
'''

@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="save", help=saveDocString)
async def saveLocation(ctx, locationName: str, locationCoords: str): 
    coordCheck = isCorrectCoordFormat(locationCoords)
    nameCheck = isCorrectLength(locationName)
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


@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="get", help=getDocString)
async def getLocation(ctx, locationName: str):
    nameCheck = isCorrectLength(locationName)
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

        

@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="delete", help=deleteDocString)
async def deleteLocation(ctx, locationName: str):
    nameCheck = isCorrectLength(locationName)
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
            

@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="update", help=updateDocString)
async def updateLocation(ctx, locationName, newCoords):
    nameCheck = isCorrectLength(locationName)
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


'''
TODO
Scale this function in the future
'''
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="list", help=listDocString)
async def list_locations_for_player(ctx):
    try:
        player_locations = list_locations(ctx.author.id)
        if len(player_locations) >= 1:
            await ctx.send(embed=makeEmbed(description=player_locations, authorName=ctx.author.display_name))
        else:
            await ctx.send(embed=makeErrorEmbed("You have no locations to list."))
    except ClientError as e:
        await ctx.send(embed=makeErrorEmbed("Try this command again later.", {e}))
        

'''
Start S3 Functions
'''

@commands.cooldown(RATE, PER * 2, commands.BucketType.user)
@bot.command(name="saveImg", help=saveImgDocString)
async def saveImage(ctx, location_name):
    nameCheck = isCorrectLength(location_name)
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

@commands.cooldown(RATE, PER * 2, commands.BucketType.user)
@bot.command(name="deleteImg", help=deleteImgDocString)
async def deleteImage(ctx, locationName):
    nameCheck = isCorrectLength(locationName)
    if nameCheck is not True:
        await ctx.send(embed=makeErrorEmbed("Error", nameCheck))
    else:
        try:
            await delete_image_url(ctx.author.id, locationName)
            await ctx.send(embed=makeEmbed("Successful image deletion.", f"For location {locationName}", ctx.author.display_name))
        except Exception as e:
            await ctx.send(embed=makeErrorEmbed("Error deleting image.", str(e)))


'''
Start seed functions
'''

@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="ss", help=setSeedDocString)
async def setSeed(ctx, seed: str):
    if validate_seed(seed):
        setSeedAttempt = set_seed(ctx.author.id, to_minecraft_seed(seed))
        # update the cache when set_seed is called
        cache_user_seed(ctx.author.id, seed)
        # res 0 contains a success/error message
        if setSeedAttempt[1] == True:
            await ctx.send(embed=makeEmbed(title=setSeedAttempt[0]))
        else:
            await ctx.send(embed=makeEmbed(title=setSeedAttempt[0]))
        

# Utility fn for users to see their set seed, more for completeness
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="gs", help=getSeedDocString)
async def getSeed(ctx):
    cached_seed = get_cached_seed(ctx.author.id)
    if cached_seed is not None:
         await ctx.send(embed=makeEmbed("Retrieved Seed", f"{cached_seed}"))
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
    await interaction.response.defer() 
    await interaction.followup.send(
        f"Searching for nearest **{feature}** near ({x_coord}, {z_coord}) within {radius} blocks."
    )
    arguments = [interaction.command.name, feature, x_coord, z_coord, radius]
    # locateBiomes library fn takes a Y coordinate, doesn't seem to affect outcome of search though
    if feature in BIOMES:
        arguments.insert(3, 0)
    seedInfo = connectToInputHandler(interaction.user.id, arguments)
    formatted_res = f"Found {seedInfo['feature']} at ({seedInfo['x']}, {seedInfo['z']})"
    await interaction.followup.send(embed=makeEmbed("Retrieved Coordinates", formatted_res, interaction.user.name))

'''
Start utility fns
'''
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="helpme", help=helpDocString)
async def help_command(ctx):
    COLOR = 0x115599
    commands_list = [cmd for cmd in ctx.bot.commands if not cmd.hidden]
    # 5 commands per page
    pages = [commands_list[i:i+5] for i in range(0, len(commands_list), 5)]
    embeds = []

    for page in pages:
        desc = ""
        for cmd in page:
            desc += f"**!{cmd.name}** - {cmd.help or 'No description provided.'}\n"
        embed = Embed(title="Lapis' Commands", description=desc, color=COLOR)
        embeds.append(embed)
        
    await ctx.send(embed=embeds[0], view=HelpPaginator(embeds=embeds))


@bot.command(name="logout", help="Logs the bot out of Discord. Bot owner only.")
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
        
bot.run(TOKEN)
'''
python3 -m src.lapis.lapis
'''

