# needed since load_dotenv is only called in lapis.py -  a different module not used by tests
from dotenv import load_dotenv
load_dotenv()

def ensure_env_vars_loaded():
    import os
    required_vars = ['REGION_NAME', 'TOKEN', 'BUCKET_NAME']
    for var in required_vars:
        if not os.getenv(var):
            raise RuntimeError(f"Missing required env var: {var}")