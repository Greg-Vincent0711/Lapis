# Connects to Cubiomes Backend
import subprocess
import json

def run_seedinfo_command(args: list[str]) -> dict:
    result = subprocess.run(
        ["./SeedInfoFns"] + args,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"SeedInfoFns failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid output from SeedInfoFns: {result.stdout.strip()}")
