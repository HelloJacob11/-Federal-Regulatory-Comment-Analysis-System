import requests
import json
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv('REGULATIONS_API_KEY')