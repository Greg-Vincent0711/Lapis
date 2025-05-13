import os
import discord
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument
from lapis.helpers.utils import *
from lapis.helpers.docstrings import *
from lapis.helpers.exceptions import *
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from lapis.helpers.embed import *
from discord.ext import commands
from lapis.backend.db import *

'''
TODO
Seed Integration with Cubiomes-based code
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
    print(f'{bot.user.name} has connected to Discord!')

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
            await ctx.send(embed=makeEmbed(title=f"{locationName} has been saved.", authorName=ctx.author.display_name, description=formattedCoords, requestedBy=True))
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
                    await ctx.send(embed=makeEmbed(title=f"Coordinates for {locationName}", authorName=ctx.author.display_name, description=f"{retrieved_data[0]}", requestedBy=True, url=retrieved_data[1]))
                else:
                    await ctx.send(embed=makeEmbed(title=f"Coordinates for {locationName}", authorName=ctx.author.display_name, description=f"{retrieved_data[0]}", requestedBy=True))
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
                await ctx.send(embed=makeEmbed(title="Success", authorName=ctx.author.display_name, description=result, requestedBy=True))
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
                await ctx.send(embed=makeEmbed(title=f"{locationName} updated successfully.", authorName=ctx.author.display_name, description=f"New coordinates: {response}", requestedBy=True))
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
            await ctx.send(embed=makeEmbed(description=player_locations, authorName=ctx.author.display_name, requestedBy=True))
        else:
            await ctx.send(embed=makeErrorEmbed("You have no locations to list."))
    except ClientError as e:
        await ctx.send(embed=makeErrorEmbed("Try this command again later.", {e}))

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
            await ctx.send(embed=makeEmbed("Successful image deletion.", ctx.author.display_name, f"For location {locationName}", requestedBy=True))
        except Exception as e:
            await ctx.send(embed=makeErrorEmbed("Error deleting image.", str(e)))
        

@commands.cooldown(RATE, PER, commands.BucketType.user)
@bot.command(name="nearest", help="")
# async def nearest(ctx, )

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

    await ctx.send(embed=makeEmbed(title="Lapis' Commands", description=help_text))

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
    
