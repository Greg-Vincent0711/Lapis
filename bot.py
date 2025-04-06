import os
import discord
import boto3
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument
import requests
from utils import *
from docstrings import *
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from encryption import encrypt, decrypt, generate_hash
from discord.ext import commands
from boto3.dynamodb.conditions import Key
from io import BytesIO

'''
TODO
s3 operations
refactoring of updateLocation - by location name or coordinates
delay between commands for a user so they can't be spammed
text embeds to make bot responses look better
'''
load_dotenv()
TOKEN = os.getenv('TOKEN')
BUCKET = os.getenv('BUCKET_NAME')
dbInstance = boto3.resource('dynamodb')
s3Instance = boto3.resource('s3')
TABLE = dbInstance.Table(os.getenv('TABLE_NAME'))

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name="saveLocation", help=saveDocString)
async def saveLocation(ctx, locationName: str, locationCoords: str): 
    print("from save location" + locationCoords)   
    coordFormatMsg = isCorrectCoordFormat(locationCoords)
    nameLengthVar = isCorrectLength(locationName)

    # both of these fns return error messages if not True
    if nameLengthVar is not True:
        await ctx.send(f"{nameLengthVar}")
    
    elif coordFormatMsg is not True:
        await ctx.send(f"{coordFormatMsg}")
        
    else:
        try:
            TABLE.put_item(
            Item={
                "Author_ID": str(ctx.author.id),
                "Location" : generate_hash(locationName),
                "Location_Name": encrypt(locationName).decode(),
                "Coordinates": encrypt(locationCoords).decode(),
            }
        )
            await ctx.send(f"{ctx.author.name}, your new location `{locationName}` has been saved!")
        except ClientError as e:
            await ctx.send(f'Error saving your location: {e}')

@bot.command(name="getLocation", help=getDocString)
async def getLocation(ctx, locationName: str):
    nameLengthVar = isCorrectLength(locationName)
    if nameLengthVar is not True:
        await ctx.send(f"{nameLengthVar}")
    else:
        try:  
            response = TABLE.get_item(
                Key={
                    "Author_ID": str(ctx.author.id),
                    "Location": generate_hash(locationName)
                }
            )
            if 'Item' in response:
                encryptedCoordinates = response['Item']['Coordinates']
                retrieved_coordinates = decrypt(encryptedCoordinates.encode()).decode()
                await ctx.send(f"Found coordinates: '{retrieved_coordinates} for location {locationName}'")
            else:
                await ctx.send(f"No location named {locationName} has been found. Check your spelling.")
        except ClientError as e:
            print(f'{e}')
            await ctx.send(f'Error getting locations, try again later.')

        


@bot.command(name="deleteLocation", help=deleteDocString)
async def deleteLocation(ctx, locationName: str):
    nameLengthVar = isCorrectLength(locationName)
    if nameLengthVar is not True:
        await ctx.send(f"{nameLengthVar}")
    else:
        try:
            deletion_response = TABLE.delete_item(
                Key={
                    "Author_ID": str(ctx.author.id),
                    "Location": generate_hash(locationName)
                },
                ReturnValues="ALL_OLD"
            ),
            
            if "Attributes" in deletion_response:
                print("Item was deleted:", deletion_response["Attributes"])
                await ctx.send(f"{locationName} has been deleted.")
            else:
                await ctx.send(f"No matching location found for {locationName}. Call !list to see all locations you have created.")
        except ClientError as e:
            error_message = e.response["Error"]["Message"]
            print(f'Error: {error_message}')
            await ctx.send(f'Error deleting {locationName}: {error_message}.')


@bot.command(name="updateLocation", help=updateDocString)
async def updateLocation(ctx, locationName, new_coordinates):
    nameLengthVar = isCorrectLength(locationName)
    if nameLengthVar is not True:
        await ctx.send(f"{nameLengthVar}")
    else:
        try:
            item_to_update = TABLE.update_item(
                Key={
                    "Author_ID" : str(ctx.author.id),
                    "Location" : generate_hash(locationName)
                },
                UpdateExpression="set Coordinates = :newCoords",
                ExpressionAttributeValues={
                    ":newCoords": encrypt(new_coordinates).decode()
                },
                ReturnValues="UPDATED_NEW"
            )
            if "Attributes" in item_to_update:
                    await ctx.send(f"{locationName} updated successfully. New coordinates: {item_to_update['Attributes']['Coordinates']}")
            else:
                await ctx.send(f"{locationName} update attempted, but no values were returned. Double-check if it exists with !list.")

        except ClientError as e:
            error_message = e.response["Error"]["Message"]
            print(f'Error: {error_message}')
            await ctx.send(f'Error updating {locationName}: {error_message}. Check your spelling or try again.')


@bot.command(name="list", help=listDocString)
async def list_locations_for_player(ctx):
    try:
        response = TABLE.query(
            KeyConditionExpression=Key("Author_ID").eq(str(ctx.author.id))
        )
        # decrypt(encryptedCoordinates.encode()).decode()
        encrypted_locations = [val for val in response['Items']]
        player_locations = extract_decrypted_locations(encrypted_locations)
        if len(player_locations) >= 1:
            await ctx.send(player_locations)
        else:
            await ctx.send("You don't have any locations created.")
    except ClientError as e:
        print(f'{e}')

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

    await ctx.send(help_text)

@bot.command(name="logout", help="Logs the bot out of Discord. Bot owner only.")
@commands.is_owner()
async def logout(ctx):
    await ctx.send("Logging out...")
    await bot.close()
    

# @bot.command(name="saveImage")
# async def uploadImage(message):
#     if message.author.bot:
#         return
    
#     if message.attachment.content_type.startswith("image/"):
#         img_data = requests.get(message.attachment.url).content
#         filename = f"uploads/{message.attachment.filename}"
#         try:
#             s3Instance.upload_fileobj(BytesIO(img_data), BUCKET, filename, ExtraArgs={"ACL": "public-read"})
#             s3_url = f"https://{BUCKET}.s3.amazonaws.com/{filename}"
#             response = dbInstance.updateItem(Key={
                
#             })
#         except Exception as e:
#             print(e)
        
#         await message.channel.send(f"Image uploaded, access it here: {s3_url}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send("That command doesn't exist. Send `!helpme` for a list of all commands.")

    elif isinstance(error, MissingRequiredArgument):
        await ctx.send("You're missing a required argument. Check `!helpme` for the proper format.")

    elif isinstance(error, BadArgument):
        await ctx.send("Invalid argument type. Please check your input.")

    else:
        await ctx.send(f"An error occurred: {error}")
        
bot.run(TOKEN)