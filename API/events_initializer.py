# Import necessary packages
import semantic_kernel as sk  # Import the semantic_kernel library
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion  # Import OpenAIChatCompletion from the semantic_kernel library

""" 
# COMMENTED OUT DUE TO IRRELEVANCE/ERRORS
from semantic_kernel import PromptTemplateConfig, PromptTemplate, SemanticFunctionConfig  # Import additional classes from semantic_kernel
from sklearn.feature_extraction.text import TfidfVectorizer  # Import TfidfVectorizer for text vectorization
from sklearn.metrics.pairwise import cosine_similarity  # Import cosine_similarity for computing similarity between texts

 """
import random  # Import random module for generating random numbers
import time  # Import time module for time-related tasks
import asyncio
import webbrowser
import datetime

import gcal_scraping_quickstart as gcal;

# Placeholders @Prakhar
WEIGHT = 0.5
API_KEY = ""
ORG_ID = ""

class EventInitializer:

    def __init__(self):
        self.service = gcal.get_service()
        self.weight = WEIGHT  # Set the weight (e.g., 0.1, 0.2, 0.8)
       
        
        self.kernel = sk.Kernel()  # Initialize a semantic kernel

        # COMMENTED OUT DUE TO LACK OF VALID API KEY @Prakhar
        #self.kernel.add_service("chat-gpt", OpenAIChatCompletion("gpt-4-1106-preview", API_KEY, ORG_ID))  # Add OpenAI chat service to the kernel

    # For @Prakhar
    async def addEventAIServer(self, action):
        pass
    
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
    return event_body['summary'] and event_body['start'] and event_body['end']

# Testing

def main():
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

if __name__ == "__main__":
  main()
  