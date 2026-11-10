# makes `import src.lapis...` work no matter where pytest is started from
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

# needed since load_dotenv is only called in lapis.py -  a different module not used by every test
from dotenv import load_dotenv
load_dotenv()
