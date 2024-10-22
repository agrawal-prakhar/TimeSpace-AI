
import os
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
import json
import pytz

# Load environment variables from the .env file
load_dotenv()

# Retrieve API keys from environment variables
API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_CONFIG = {
   "temperature": 1,
   "top_p": 0.95,
   "top_k": 64,
   "max_output_tokens": 8192,
   "response_mime_type": "text/plain",
} 

class ModelInitializer:
   def __init__(self, system_instruction, model_name=DEFAULT_MODEL, config_mods={}):
      self.model = genai.GenerativeModel(
         model_name=model_name,
         generation_config=DEFAULT_CONFIG | config_mods, # simply pass in the properties you want to modify from the default in as a new object
         system_instruction=system_instruction
      )

# SOME MODELS MAY BE MORE CONDUCIVE TO MAKING A CHAT THREAD, BUT SOME MAY BE CONDUCIVE TO SIMPLE "generate_content" CALL