import os 
from dotenv import load_dotenv

load_dotenv()

class Config():
    MONGO_URI = os.getenv("MONGO_URI")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET")
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")
    HOST = os.getenv("HOST")

