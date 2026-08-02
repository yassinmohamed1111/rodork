import os
from dotenv import load_dotenv

load_dotenv()

SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
if not SHODAN_API_KEY:
    raise RuntimeError("SHODAN_API_KEY not found. Set it in .env file.")
