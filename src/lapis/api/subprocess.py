import subprocess
import json
import os
from src.lapis.api.services.db.db_services import retrieve_seed

# spawn_near can scan up to a million seeds. The seed Lambda is killed after 10 seconds
# (FormationTemplate.YAML), so stop a little earlier and answer with a readable error instead.
# Hosts without that limit (the bot) can raise it with the SEED_TOOL_TIMEOUT env var.
DEFAULT_TIMEOUT_SECONDS = 8

def connectToInputHandler(author_id: str, args: list[str]) -> list[dict]:
    """
    Runs the compiled C program (SeedInfoFns/inputHandler) as: <executable> <seed> <args...>
    and returns whatever JSON it printed, always as a list of dicts.
    Raises NotFoundError if the user hasn't set a seed yet.
    """
    # replacing cache fn, refer to cache.py to see why
    # retrieve_seed returns the decrypted, numeric seed string
    seed = retrieve_seed(author_id)
    executable = os.getenv("EXECUTABLE_NAME")
    if not executable:
        raise ValueError("EXECUTABLE_NAME is not set, so the seed tools can't be run.")
    # *map spread all args into their individual forms as strings
    fullList = [executable, seed, *map(str, args)]
    try:
        result = subprocess.run(
            fullList,
            capture_output=True,
            text=True,
            timeout=float(os.getenv("SEED_TOOL_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)),
        )
    except subprocess.TimeoutExpired:
        raise ValueError("That search took too long. Try a more common biome or structure, or a different range.")
    except OSError as e:
        # missing file, or a binary compiled for a different OS/CPU than this machine
        raise ValueError(f"Could not run the seed tools executable at '{executable}': {e}")

    output = result.stdout.strip()
    # nearestStructure.c prints a plain "Couldn't find..." line to stdout whenever a search
    # misses, in front of the JSON. Skip ahead to where the JSON actually starts.
    json_starts = [i for i in (output.find("{"), output.find("[")) if i != -1]
    if not json_starts:
        return []
    try:
        resFromHandler = json.loads(output[min(json_starts):])
        # errors from c code are passed as an object. We need a list.
        if not isinstance(resFromHandler, list):
            resFromHandler = [resFromHandler]
        return resFromHandler
    except json.JSONDecodeError as e:
        # Handle malformed JSON
        print(f"Error: {e}")
        raise ValueError(f"Invalid output from SeedInfoFns: {output}")
