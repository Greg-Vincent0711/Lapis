# needed since load_dotenv is only called in lapis.py -  a different module not used by tests
from dotenv import load_dotenv
load_dotenv()