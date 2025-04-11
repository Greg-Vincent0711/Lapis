import os
import discord
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument
from utils import *
from docstrings import *
from exceptions import *
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from embed import *
from discord.ext import commands
from db import *

'''
TODO
s3 operations
Map integration with Dynmap, Chunkbase maybe
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
    print(f'{bot.user.name} has connected to Discord!')

@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="save", help=saveDocString)
async def saveLocation(ctx, locationName: str, locationCoords: str): 
    coordCheck = isCorrectCoordFormat(locationCoords)
    nameCheck = isCorrectLength(locationName)
    # both of these fns return error messages if not True
    if nameCheck is not True:
        await ctx.send(f"{nameCheck}")
    
    elif coordCheck is not True:
        await ctx.send(f"{coordCheck}")
    else:
        try:
            formattedCoords = format_coords(locationCoords)
            save_location(ctx.author.id, locationName, formattedCoords)
            await ctx.send(embed=makeEmbed(f"{locationName} has been saved.", ctx.author.display_name, formattedCoords, requestedBy=True))
        except Exception as e:
            await ctx.send(embed=makeErrorEmbed("Error saving your message.", {e}))


@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="get", help=getDocString)
async def getLocation(ctx, locationName: str):
    nameCheck = isCorrectLength(locationName)
    if nameCheck is not True:
        await ctx.send(f"{nameCheck}")
    else:
        try:
            # always contains coordinates, may contain an image URL 
            retrieved_data = get_location(ctx.author.id, locationName)
            if retrieved_data is not None: 
                url = retrieved_data[1] if retrieved_data[1] is not None else None
                await ctx.send(embed=makeEmbed(f"{retrieved_data[0]}", ctx.author.display_name, requestedBy=True, url=url))
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
            deleted_coords = delete_location(ctx.author.id, locationName)
            if deleted_coords != None:
                await ctx.send(embed=makeEmbed(f"{locationName} has been deleted.", ctx.author.display_name, deleted_coords, requestedBy=True))
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
                await ctx.send(embed=makeEmbed(f"{locationName} updated successfully.", ctx.author.display_name, f"New coordinates: {response}", requestedBy=True))
            else:
                await ctx.send(embed=makeErrorEmbed(f"Error updating {locationName}"))
        except ClientError as e:
            error_message = e.response["Error"]["Message"]
            await ctx.send(embed=makeErrorEmbed(f'Error updating {locationName}', error_message))

@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="list", help=listDocString)
async def list_locations_for_player(ctx):
    try:
        player_locations = list_locations(ctx.author.id)
        if len(player_locations) >= 1:
            await ctx.send(embed=makeEmbed(description=player_locations, requestedBy=True))
        else:
            await ctx.send(embed=makeErrorEmbed("You have no locations to list."))
    except ClientError as e:
        await ctx.send(embed=makeErrorEmbed("Try this command again later.", {e}))

@commands.cooldown(RATE, PER * 2, commands.BucketType.user)
@bot.command(name="saveImage", help=saveDocString)
async def saveImage(ctx, location_name):
    try:
        message = ctx.message
        author_id = ctx.author.id
        result = await save_image_url(author_id, location_name, message)
        if result:
            await ctx.send(embed=makeEmbed(f"{location_name} now has a corresponding image."))
        else:
            await ctx.send(embed=makeErrorEmbed("Image not saved", "Failed to update the database."))
    except (ValueError, InvalidImageFormatError, ImageDownloadError, S3UploadError) as e:
        print(e)
        await ctx.send(embed=makeErrorEmbed("Error saving your image.", str(e)))
        
@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="helpme", help=helpDocString)
async def help_command(ctx):
    help_text = (
        "Commands are always in one of these forms:\n"
        "`!command location_name 'x y z'`\n"
        "`!command location_name`\n"
        "`!command`\n\n"
    )
    for command in bot.commands:
        if not command.hidden:
            help_text += f"**!{command.name}** - {command.help or 'No description provided.'}\n"

    await ctx.send(embed=makeEmbed("Lapis' Commands", help_text))

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
    
