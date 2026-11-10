from typing import Optional
from src.lapis.helpers.utils import *
from src.lapis.api.subprocess import connectToInputHandler

# the C code returns this for both coordinates when a search finds nothing (-INT_MAX)
NOT_FOUND_COORD = -2147483647

def _error_from(results: list[dict]) -> str | None:
    """The C code reports problems under a few different keys. Returns the message, or None if all is well."""
    if not results:
        return "The seed tools returned no results."
    first = results[0]
    for key in ("Error", "error", "message", "usage"):
        if key in first:
            return str(first[key])
    return None

def nearest_impl(author_id: str, feature: str, x_coord: str, z_coord: str, radius: str):
    """
    Finds the nearest biome or structure to (x, z) in the user's saved seed.
    Returns {"result": ...} on success or {"Error": ...} on failure.
    """
    feature_formatted = format_feature(feature)
    if is_structure(feature):
        # structures are searched in 2D: nearest <structure> x z radius
        arguments = ["nearest", feature_formatted, x_coord, z_coord, radius]
    else:
        # biomes also take a height: nearest <biome> x y z radius
        # 64 is ground level. Doesn't affect outcome
        arguments = ["nearest", feature_formatted, x_coord, "64", z_coord, radius]

    seedInfo = connectToInputHandler(author_id, arguments)
    error = _error_from(seedInfo)
    if error:
        if error == "Incorrect usage.":
            error = f"'{feature}' isn't a biome or structure Lapis can search for."
        return {"Error": error}

    found = seedInfo[0]
    if found["x"] == NOT_FOUND_COORD or found["z"] == NOT_FOUND_COORD:
        return {"Error": f"No {feature} found within {radius} blocks of ({x_coord}, {z_coord})."}

    formatted_res = f"Found {found['feature']} at ({found['x']}, {found['z']})"
    return {"result": formatted_res}


def spawn_near_impl(author_id: str, numseeds: str, range_val: str,
                    biome: Optional[str] = "None", structure: Optional[str] = "None"):
    """
    Finds seeds whose spawn point is in a biome and/or within range_val blocks of a structure.
    Returns {"result": ...} on success or {"Error": ...} on failure.
    """
    try:
        numseeds_int, range_int = int(numseeds), int(range_val)
    except (TypeError, ValueError):
        return {"Error": "The number of seeds and the range must both be whole numbers."}
    arguments = ["spawn_near", numseeds_int, format_feature(biome), format_feature(structure), range_int]

    retrievedSeeds = connectToInputHandler(author_id, arguments)
    error = _error_from(retrievedSeeds)
    if error:
        return {"Error": error}

    formatted_res = ""
    for seed in retrievedSeeds:
        formatted_res += f"{seed['seed']} with spawn {seed['spawn']['x']},{seed['spawn']['z']}\n"

    return {"result": formatted_res}
