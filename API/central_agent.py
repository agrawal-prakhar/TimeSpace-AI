import json
import asyncio
from gcal_scraper import GcalScraper
from events_initializer import EventInitializer
from gcal_service import GoogleCalendarService
from events_editor import EventEditor  # Import EventEditor to handle event editing
import google.generativeai as genai
import textwrap


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

            if task_type == "retrieve":
                await self.fetch_events(task.get("date"))
            elif task_type == "schedule":
                await self.create_event(task.get("eventDetails"))
            elif task_type == "edit":
                await self.edit_event(task.get("eventDetails"))
            else:
                print(f"Unknown task type: {task_type}")

    # Fetch events from the calendar using GcalScraper
    async def fetch_events(self, date):
        print(f"Fetching events for {date}...")
        events = self.gcal_scraper.get_events_on_date(date)
        if events:
            for event in events:
                print("Event:", event.get('summary', 'No Title'))
                print("Start:", event['start'].get('dateTime', 'All-day event'))
                print("End:", event['end'].get('dateTime', 'All-day event'))
                print()
        else:
            print(f"No events found for {date}")

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
    central_agent.upload_input_text("Retrieve events for 2024-10-20 and schedule a meeting tomorrow with John. Edit the event if necessary.")

    # Assign tasks based on the input text
    await central_agent.assign_tasks()

if __name__ == "__main__":
    asyncio.run(main())
