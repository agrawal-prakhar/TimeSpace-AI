import webbrowser
import datetime

import gcal_scraping_quickstart as gcal;
import semantic_kernel as sk 

from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig, pipeline, BitsAndBytesConfig
import random  # Import random module for generating random numbers
import time  # Import time module for time-related tasks
import asyncio
import webbrowser
import datetime
from huggingface_hub import login
from langchain_huggingface import HuggingFacePipeline
import semantic_kernel.connectors.ai.hugging_face as sk_hf

import gcal_scraping_quickstart as gcal;
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Retrieve Hugging Face token from environment variables
hf_token = os.getenv('HF_TOKEN')
login(hf_token)
model_name = "microsoft/Phi-3.5-mini-instruct"
    
bnb_config = BitsAndBytesConfig()

model = AutoModelForCausalLM.from_pretrained(model_name,
                                                 device_map="auto",
                                                 config=bnb_config,
                                                 trust_remote_code=True)

gen_cfg = GenerationConfig.from_pretrained(model_name)
gen_cfg.max_new_tokens = 256
gen_cfg.temperature = 0.0000001 
gen_cfg.return_full_text = True
gen_cfg.do_sample = True
gen_cfg.repetition_penalty = 1.11
    
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

pipe = pipeline(
        task="text-generation",
        model=model,
        tokenizer=tokenizer,
        generation_config=gen_cfg
    )

#llm = HuggingFacePipeline(pipeline=pipe)

# Access the API Key and Org ID
# API_KEY = os.getenv("OPENAI_API_KEY")
# ORG_ID = os.getenv("OPENAI_ORG_ID")
class HuggingFacePipelineService:
    def __init__(self, pipeline, service_id):
        self.pipeline = pipeline
        self.service_id = service_id

    def generate(self, input_text):
        return self.pipeline(input_text)

class EventInitializer:

    def __init__(self):
        self.service = gcal.get_service()
       
        
        self.kernel = sk.Kernel()  # Initialize a semantic kernel

        # Configure LLM service
        # self.kernel.config.add_text_completion_service(
        #     "llm", sk_hf.HuggingFaceTextCompletion("llm", task="text-generation")
        # )

        # self.kernel.config.add_text_embedding_generation_service(
        #     "microsoft/Phi-3.5-mini-instruct",
        #     sk_hf.HuggingFaceTextEmbedding("microsoft/Phi-3.5-mini-instruct"),
        # )
        # self.kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())
        # self.kernel.import_skill(sk.core_skills.TextMemorySkill())

        huggingface_service = HuggingFacePipelineService(pipe, "huggingface_llm")


        self.kernel.add_service(huggingface_service) # Add phi-mini chat service to the kernel

    # For @Prakhar
    async def addEventAIServer(self, action):

        prompt = f"""
            You are a calendar assistant. Based on the following input: '{action}', generate the required JSON for a Google Calendar event.
            The JSON should contain:
            - "summary": a short title for the event,
            - "start": the start time in ISO 8601 format,
            - "end": the end time in ISO 8601 format,
            - "timeZone": the time zone for the event.

            An example format is this:
                        {{
                    'summary': 'Work on TimeSpace',
                    'start': {{
                        'dateTime': datetime.datetime.utcnow().isoformat() + "Z",
                        'timeZone': 'America/New_York',
                    }},
                    'end': {{
                        'dateTime': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + "Z",
                        'timeZone': 'America/New_York',
                    }},
                }}
            
            """
        huggingface_service = self.kernel.get_service("huggingface_llm")
        print(prompt)
        response = huggingface_service.generate(prompt)
        return response
    
    # Method to insert new event with specified parameters, NO ERROR HANDLING YET
    def add_event(self, event_body):
        if not validate_event_body(event_body): return False # validate
        
        event = self.service.events().insert(calendarId='primary', body=event_body).execute() # insert

        print ('Event created: %s' % event.get('htmlLink'))
        webbrowser.open(event.get('htmlLink')) # navigate user to event in GCal UI (potential pitfall of opening in browser window that is logged into another Google account)
    
    # Testing method to check scopes 
    def check_scopes(self):
        print(self.service.calendarList().get(calendarId='primary').execute())


# Helper method to validate event specifications, could be modified specifically for the logic that will control the user being prompted for more info
def validate_event_body(event_body):
    try:
        return event_body['summary'] and event_body['start'] and event_body['end']
    finally:
        return False

# Testing

async def main():
    agent = EventInitializer()
    agent.add_event(event_body={ # sample event for the next hour
        'summary': 'Work on TimeSpace',
        'start': {
            'dateTime': datetime.datetime.utcnow().isoformat() + "Z",
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat() + "Z",
            'timeZone': 'America/New_York',
        },
    }) # sample add

    event_body =  await agent.addEventAIServer("Schedule a meeting tomorrow from 10 AM to 11 AM tomorrow with John")
    print("Event body: ", event_body)
    agent.add_event(event_body)

if __name__ == "__main__":
  asyncio.run(main())
  