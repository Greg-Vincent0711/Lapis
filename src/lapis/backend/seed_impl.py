from typing import Optional
from src.lapis.helpers.utils import *
from src.lapis.backend.subprocess import connectToInputHandler
from src.lapis.helpers.features import *

def nearest_impl(author_id: str, feature: str, x_coord: str, z_coord: str, radius: str):
    """
    Decoupled version of nearest_impl for Lambda.
    Returns a dict with results or error.
    """
    arguments = [feature, x_coord, z_coord, radius]

    feature_formatted = format_feature(feature=feature)
    if feature_formatted in BIOMES:
        # locateBiomes library fn takes a Y coordinate, doesn't seem to affect outcome
        arguments = [feature_formatted, x_coord, "0", z_coord, radius]
    arguments.insert(1, feature_formatted)

    seedInfo = connectToInputHandler(author_id, arguments)
    
    if "error" in seedInfo:
        return {"error": seedInfo["error"]}

    formatted_res = f"Found {seedInfo['feature']} at ({seedInfo['x']}, {seedInfo['z']})"
    return {"result": formatted_res}


def spawn_near_impl(author_id: str, numseeds: str, range_val: str,
                    biome: Optional[str] = "None", structure: Optional[str] = "None"):
    """
    Decoupled version of spawn_near_impl for Lambda.
    Returns a dict with results or error.
    """
    range_val = int(range_val)
    arguments = ["spawn_near", numseeds, format_feature(biome), format_feature(structure), range_val]

    retrievedSeeds = connectToInputHandler(author_id, arguments)

    if not retrievedSeeds or "error" in retrievedSeeds[0]:
        return {"error": retrievedSeeds[0].get("error", "Unknown error")}

    formatted_res = ""
    for seed in retrievedSeeds:
        formatted_res += f"{seed['seed']} with spawn {seed['spawn']['x']},{seed['spawn']['z']}\n"

    return {"result": formatted_res}
