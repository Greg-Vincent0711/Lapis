import os
import discord
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

dbConnection = boto3.resource('dynamodb')
dataTable = dbConnection.Table(os.getenv('TABLE_NAME'))


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    

@bot.command()
async def newLocation(ctx, locationName: str, locationCoords: str):
    try:
        dataTable.put_item(
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
        response = dataTable.get_item(
            Key={
                'Author_ID': str(ctx.author.id),
                'Location': locationName
            }
        )
        if response and response['item']:
            await ctx.send(f"Found:\nLocation: {response['Item']['Location']}  Coordinates: {response['Item']['Coordinates']}")
        else:
            await ctx.send(f"No location named {locationName} has been found. Check your spelling.")
    except ClientError as e:
        print(f'{e}')
        await ctx.send(f'Error getting locations, try again later.')


@bot.command()
async def deleteLocation(ctx, locationName: str):
    try:
        response = dataTable.delete_item(
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
    

bot.run(TOKEN)
