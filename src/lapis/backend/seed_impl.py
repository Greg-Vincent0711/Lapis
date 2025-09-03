'''
split up seedInfoFn implementations to make testing easier
fixes an issue where testing with @bot.command.tree keeps the fn from being callable
'''

import os
from typing import Optional
import discord
from src.lapis.helpers.utils import *
from src.lapis.helpers.docstrings import *
from src.lapis.helpers.exceptions import *
from src.lapis.helpers.embed import *
from src.lapis.helpers.paginator import *
from src.lapis.backend.db import *
from src.lapis.backend.cache import *
from src.lapis.backend.subprocess import connectToInputHandler
from src.lapis.helpers.features import *


def retrieveEnv():
    return os.getenv("SPN", "spawn_near")

async def nearest_impl(interaction: discord.Interaction, feature: str, x_coord: str, z_coord: str, radius: str):
    await interaction.response.defer() 
    await interaction.followup.send(
        f"Searching for nearest **{feature}** near ({x_coord}, {z_coord}) within {radius} blocks..."
    )
    arguments = [interaction.command.name, x_coord, z_coord, radius]
    # converted from a more readable format before passing to subprocess.py
    feature = format_feature(feature=feature)
    if feature in BIOMES:
        # locateBiomes library fn takes a Y coordinate, doesn't seem to affect outcome of search
        arguments.insert(3, 0)
    arguments.insert(1, feature)       
    seedInfo = connectToInputHandler(interaction.user.id, arguments)
    print(seedInfo)
    if seedInfo["error"]:
            await interaction.followup.send(embed=makeErrorEmbed("Error", seedInfo["error"]))
    formatted_res = f"Found {seedInfo['feature']} at ({seedInfo['x']}, {seedInfo['z']})"
    await interaction.followup.send(embed=makeEmbed("Retrieved Coordinates", formatted_res, interaction.user.name))


async def spawn_near_impl(interaction: discord.Interaction, numseeds: str, range: str, biome: Optional[str] = "None", structure: Optional[str] = "None"):
    range = int(range)
    await interaction.response.defer()
    await interaction.followup.send(f"Finding {numseeds} seeds with: a {biome} spawn, and a {structure} within {range} blocks...")
    arguments = ["spawn_near", numseeds, format_feature(biome), format_feature(structure), range]
    retrievedSeeds = connectToInputHandler(interaction.user.id, arguments)
    if not "error" in retrievedSeeds[0]:
        formattedRes = ""
        for seed in retrievedSeeds:
            formattedRes += f"{seed['seed']} with spawn {seed['spawn']['x']},{seed['spawn']['z']}\n"
        await interaction.followup.send(embed=makeEmbed("Found Seeds", formattedRes, interaction.user.name))
    else:
        await interaction.followup.send(embed=makeEmbed("Error retrieving seeds.", retrievedSeeds[0]["error"], interaction.user.name))
