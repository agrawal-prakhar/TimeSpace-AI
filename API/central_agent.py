from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import gcal_service as gcal
import asyncio
import google.generativeai as genai
import pytz
import json
import webbrowser
from semantic_kernel import Kernel
from model_initializer import ModelInitializer
from gcal_scraper import GcalScraper
from events_initializer import EventInitializer

# Central Agent to manage task assignment
class CentralAgent:
    def __init__(self):
        self.input_text = None
        self.kernel = Kernel()

    def upload_input_text(self, input_text):
        self.input_text = input_text

    async def assign_tasks(self):
        if self.input_text:
            return self.kernel.create_semantic_function(f"""
                Break down the tasks that are given in the {self.input_text} and assign them to specific agents based on the functionality and what is supposed to be done with them.
            """, max_tokens=1024)()

# General Agent (currently a placeholder, can be expanded)
class GeneralAgent:
    def __init__(self):
        self.kernel = Kernel()

# Test the functionality
async def main():
    cal_scraper = GcalScraper()
    
    # Get events on a specific date
    events = cal_scraper.get_events_on_date('2024-10-20')
    for event in events:
        print("Event:", event.get('summary', 'No Title'))
        print("Start:", event['start'].get('dateTime', 'All-day event'))
        print("End:", event['end'].get('dateTime', 'All-day event'))
        print()

    # Use EventInitializer to create an event via AI
    event_initializer = EventInitializer()
    ai_generated_event = json.loads((await event_initializer.event_init_ai_server("Schedule a meeting tomorrow with John")).text)
    event_initializer.add_event(ai_generated_event)

if __name__ == "__main__":
    asyncio.run(main())
