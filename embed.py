import discord
from discord import Color

def makeEmbed(title: str, color: discord.Color, ctx, description=None, requestedBy=False):
    return discord.Embed.from_dict({
    "title": title,
    "description": description,
    "color": color.value,
    "footer": {
        "text": f"Requested by {ctx.author.display_name}" if requestedBy == True else None,
    }
})
    
def makeErrorEmbed(title, error_msg=None):
    return discord.Embed.from_dict({
        "title": title,
        "description": error_msg,
        "color": Color.red().value
    })