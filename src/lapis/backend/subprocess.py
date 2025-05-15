'''
pull seed from SQLite(cache)
'''

import subprocess
import json
import os

def connectToInputHandler(args: list[str]) -> dict:
    result = subprocess.run(
        [os.getenv("EXECUTABLE_NAME")] + args,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"SeedInfoFns failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid output from SeedInfoFns: {result.stdout.strip()}")
