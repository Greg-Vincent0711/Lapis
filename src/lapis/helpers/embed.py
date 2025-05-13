import discord
from discord import Color

def makeEmbed(title = None, authorName = None, description=None, requestedBy=False, url=None):
    embedData = {
        "title": title,
        "description": description,
        "color": Color.blue().value,
    }
    embed = discord.Embed.from_dict(embedData)
    if requestedBy and authorName:
        embed.set_footer(text=f"Requested by {authorName}")

    if url:
        embed.set_thumbnail(url=url)    
    return embed

    
def makeErrorEmbed(title, error_msg=None):
    return discord.Embed.from_dict({
        "title": title,
        "description": error_msg,
        "color": Color.red().value
    })