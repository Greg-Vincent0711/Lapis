# Runs SeedInfoFns
import subprocess
import json
import os
from src.lapis.backend.cache import get_cached_seed
from src.lapis.helpers.features import *


def connectToInputHandler(author_id: str, args: list[str]) -> dict:
    seed = get_cached_seed(author_id)
    result = subprocess.run(
        # spread all args into their individual forms as strings
        [os.getenv("EXECUTABLE_NAME"), seed, *map (str, args)],
        capture_output=True,
        text=True
    )
    try:
        print(repr(result.stdout))
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid output from SeedInfoFns: {result.stdout.strip()}")
