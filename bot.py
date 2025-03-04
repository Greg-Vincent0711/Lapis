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
async def newLocation(ctx, *, locationName: str, locationCoords: str):
    try:
        dataTable.putItem(
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
async def getLocation(ctx, *, locationName: str):
    locationKeyExpression = dataTable.conditions.Key('Location').eq(str(locationName))
    authorIDExpression = dataTable.conditions.Key("Author.ID").eq(str(ctx.author.id))
    try:  
        response = dataTable.query(
        IndexName="Location", 
        KeyConditionExpression=locationKeyExpression & authorIDExpression)
        
        if 'Items' in response and response['Items']:
            locations = "\n".join([f"Location: {item['Location']} - Coordinates: {item['Coordinates']}" for item in response['Items']])
            await ctx.send(f"Found:\n{locations}")
        else:
            await ctx.send(f"No locations found for name {locationName}.")
    except ClientError as e:
        await ctx.send(f'Error getting locations: {e}')


@bot.command()
async def deleteLocation(ctx, *, locationName: str):
    try:
        dataTable.delete_item(
            Key={
                'Location': locationName,
                'Author_ID': ctx.author.id
            }
        )
        await ctx.send(f"{locationName} has been deleted.")
    except ClientError as e:
        await ctx.send(f'Error deleting {locationName}, check the spelling of the provided location.')
    

bot.run(TOKEN)
