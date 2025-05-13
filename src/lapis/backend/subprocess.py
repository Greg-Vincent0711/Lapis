'''
seed should be a stored variable

'''
# Connects to Cubiomes scripts
import subprocess
import json

def getSeedInfo(args: list[str]) -> dict:
    result = subprocess.run(
        ["./inputHandler"] + args,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"SeedInfoFns failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid output from SeedInfoFns: {result.stdout.strip()}")
