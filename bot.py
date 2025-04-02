import os
import discord
import boto3
import requests
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from discord.ext import commands
from io import BytesIO

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
    

@bot.command()
async def newLocation(ctx, locationName: str, locationCoords: str):
    try:
        TABLE.put_item(
        Item={
            "Author_ID": str(ctx.author.id),
            "Author_Name": f'{ctx.author.name}#{ctx.author.discriminator}',
            "Location" : locationName,
            "Coordinates": locationCoords,
        }
    )
        await ctx.send(f"{ctx.author.name}, your location `{locationName}` is saved!")
    except ClientError as e:
        await ctx.send(f'Error saving your location: {e}')

    
'''
List is returned with all locations matching a name
and still unique due to an ID
'''
@bot.command()
async def getLocation(ctx, locationName: str):
    try:  
        response = TABLE.get_item(
            Key={
                'Author_ID': str(ctx.author.id),
                'Location': locationName
            }
        )
        if response:
            await ctx.send(f"Found:\nLocation: {response}")
        else:
            await ctx.send(f"No location named {locationName} has been found. Check your spelling.")
    except ClientError as e:
        print(f'{e}')
        await ctx.send(f'Error getting locations, try again later.')


@bot.command()
async def deleteLocation(ctx, locationName: str):
    try:
        response = TABLE.delete_item(
            Key={
                'Author_ID': str(ctx.author.id),
                'Location': locationName
            }
        )
        await ctx.send(f"{locationName} has been deleted.")
        await ctx.send(f'{response}')
    except ClientError as e:
        print(f'Error: {e}')
        await ctx.send(f'Error deleting {locationName}, check your spelling.')
    

# @bot.command()
# async def updateLocation(ctx, oldLocationName, newLocationName: str):
#     try:
#         response = TABLE.update_item(
#             TableName=TABLE
#             Key={
#                 'Author_ID': str(ctx.author.id),
#                 'Location': oldLocationName
#             }
#         )
#     except ClientError as e:
#         print(f'Error: {e}')
#         await ctx.send(f'Error deleting {locationName}, check your spelling.')

    


# @bot.command()
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
        
#         await message.channel.send(f"Image uploaded: {s3_url}")

    
    

bot.run(TOKEN)
