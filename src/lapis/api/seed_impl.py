from typing import Optional
from src.lapis.helpers.utils import *
from src.lapis.backend.subprocess import connectToInputHandler
from src.lapis.helpers.features import *

def nearest_impl(author_id: str, feature: str, x_coord: str, z_coord: str, radius: str):
    """
    Decoupled version of nearest_impl for Lambda.
    Returns a dict with results or error.
    """
    # arguments = ["nearest", feature, x_coord, z_coord, radius]
    feature_formatted = format_feature(feature=feature)
    # 64 is ground level. Doesn't affect outcome
    arguments = ["nearest", feature_formatted, x_coord, "64", z_coord, radius]
    print(arguments)
    # arguments.insert(1, feature_formatted)
    seedInfo = connectToInputHandler(author_id, arguments)
    if "Error" in seedInfo[0]:
        return {"Error": seedInfo[0]["Error"]}

    formatted_res = f"Found {seedInfo[0]['feature']} at ({seedInfo[0]['x']}, {seedInfo[0]['z']})"
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

    if not retrievedSeeds or "Error" in retrievedSeeds[0]:
        return {"Error": retrievedSeeds[0].get("Error", "Unknown error")}

    formatted_res = ""
    for seed in retrievedSeeds:
        formatted_res += f"{seed['seed']} with spawn {seed['spawn']['x']},{seed['spawn']['z']}\n"

    return {"result": formatted_res}
