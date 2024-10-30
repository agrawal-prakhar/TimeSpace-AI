import json
import asyncio
from gcal_scraper import GcalScraper
from events_initializer import EventInitializer
from gcal_service import GoogleCalendarService
from events_editor import EventEditor  # Import EventEditor to handle event editing
import google.generativeai as genai
import textwrap
from model_initializer import ModelInitializer


# Central Agent to manage task assignment and coordinate agents
class CentralAgent:
    def __init__(self):
        self.input_text = None

        # Instantiate the GoogleCalendarService
        calendar_service = GoogleCalendarService()

        # Instantiate the GcalScraper using the authenticated calendar service
        self.gcal_scraper = GcalScraper(calendar_service)
        self.event_initializer = EventInitializer()  # Initialize EventInitializer for creating events
        self.event_editor = EventEditor()  # Initialize EventEditor for editing and deleting events

    # Upload input text that may contain commands for the agent to process
    def upload_input_text(self, input_text):
        self.input_text = input_text

    # Assign tasks based on the input text using Gemini AI
    async def assign_tasks(self):
        if self.input_text:
            print(f"Input: {self.input_text}")

            # Use Gemini AI to break down the input into tasks
            task_breakdown_prompt = textwrap.dedent(f"""
                Break down the tasks given in the following input: "{self.input_text}".
                Assign these tasks to specific agents based on functionality.
                Use the GcalScraper for retrieving events, the EventInitializer for scheduling or creating new events, 
                and the EventEditor for editing or deleting existing events. 
                Provide a JSON response with each task and the agent responsible. Break it down into task, type, agent, date, and event details.
            """)
            
            # Call Gemini model to generate the task breakdown
            response = self.event_initializer.model_init.model.generate_content(task_breakdown_prompt)

            # Debug the response before parsing
            print(f"Raw response from Gemini: {response.text}")

            try:
                # Attempt to parse the response as JSON
                tasks = json.loads(response.text)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                return

            # Debug the parsed tasks
            print(f"Parsed tasks: {tasks}")

            # Handle the tasks if parsed successfully
            await self.handle_tasks(tasks.get("tasks", []))

    # Handle tasks assigned to specific agents
    async def handle_tasks(self, tasks):
        for task in tasks:
            print(f"Handling task: {task}")
            task_type = task.get("type")

            if task_type == "retrieve events":
                await self.fetch_events(task.get("date"))
            elif task_type == "retrieve free times":
                await self.fetch_free_times(task.get("date"))
            elif task_type == "schedule":
                await self.create_event(task.get("eventDetails"))
            elif task_type == "edit":
                await self.edit_event(task.get("eventDetails"))
            elif task_type == "unknown task":
                continue
            else:
                print(f"Unknown task type: {task_type}")

    # Fetch events from the calendar using GcalScraper
    async def fetch_events(self, date):
        print(f"Fetching events for {date}...")
        events = self.gcal_scraper.get_events_on_date(date)
        # Use Gemini AI to determine events
        task_breakdown_prompt = f"""
            Respond to "{self.input_text}" by fetching the day's scheduled events given the following context. The events on the user's calendar are as follows: "{events}".
            Here are example responses:
            
            "On {date}, you have a phone call with Sam from 10 AM to 11 AM, a meeting with Julie from 1 PM to 2 PM, and a dinner with family from 6 PM to 8 PM."
            "You have no events scheduled for {date}."
            "The events scheduled for {date} are: a conference from 9 AM to 5 PM, reception from 6 PM to 8 PM, and a party from 8 PM to 11 PM."
        """
        
        model_init = ModelInitializer(f"""
            You are a calendar assistant. Based on the following input, respond to the query in paragraph form.
            """
        )
        
        # Call Gemini model to generate the task breakdown
        response = model_init.model.generate_content(task_breakdown_prompt)
        print("Gemini Response:", response)
        
        if events:
            for event in events:
                print("Event:", event.get('summary', 'No Title'))
                print("Start:", event['start'].get('dateTime', 'All-day event'))
                print("End:", event['end'].get('dateTime', 'All-day event'))
                print()
        else:
            print(f"No events found for {date}")
    
    # Fetch free times using GcalScraper
    async def fetch_free_times(self, date):
        print(f"Fetching free times for {date}...")
        busy_times = self.gcal_scraper.get_busy_times(date)
        
        task_breakdown_prompt = f"""
            Respond to "{self.input_text}" by fetching the day's free times given the following context. Do not tell me when I have events scheduled,
            only when I am free. The busy times on the user's calendar are as follows: "{busy_times}". Here are example responses:
            
            "On {date}, you are free from 9 AM to 10 AM and from 2 PM to 4 PM."
            "You are free all day on {date}."
            "The times you are free on {date} are as follows: 10 AM to 11 AM, 1 PM to 3 PM."
        """
        
        model_init = ModelInitializer(f"""
            You are a calendar assistant. Based on the following input, respond to the query in paragraph form.
            """
        )
        
        # Call Gemini model'
        response = model_init.model.generate_content(task_breakdown_prompt)
        print("Gemini Response:", response)
        
        if busy_times:
            for busy_time in busy_times:
                print("Busy Time:", busy_time)
        else:
            print(f"No busy times found for {date}")

    # Create an event using EventInitializer and Gemini AI
    async def create_event(self, event_details):
        print("Creating event with details:", event_details)
        ai_generated_event = json.loads((await self.event_initializer.event_init_ai_server(event_details)).text)
        self.event_initializer.add_event(ai_generated_event)

    # Edit or delete an event using EventEditor
    async def edit_event(self, event_details):
        print("Editing event with details:", event_details)

        # Fetch upcoming events before editing
        events = self.event_editor.get_events()

        # Use AI to generate an updated event body
        event_body = json.loads((await self.event_editor.event_edit_ai_server(event_details, events)).text)

        # If the event is cancelled, delete it; otherwise, update the event
        if isinstance(event_body, list):
            for single_event in event_body:
                if single_event.get('status') == 'cancelled':
                    self.event_editor.delete_event(single_event)
                else:
                    self.event_editor.update_event(single_event)
        elif isinstance(event_body, dict):
            if event_body.get('status') == 'cancelled':
                self.event_editor.delete_event(event_body)
            else:
                self.event_editor.update_event(event_body)
        else:
            print(f"Unexpected event_body format: {type(event_body)}. Expected list or dict.")

# Testing the CentralAgent functionality
async def main():
    # Initialize the CentralAgent
    central_agent = CentralAgent()

    # Simulate uploading input text to the agent
    central_agent.upload_input_text("I have an Analysis midterm on 2024-11-01 at 8 am. Please schedule the midterm and regular study sessions leading up to it.")

    # Assign tasks based on the input text
    await central_agent.assign_tasks()

if __name__ == "__main__":
    asyncio.run(main())
