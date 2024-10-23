import webbrowser
import datetime
import asyncio
import json
from gcal_service import GoogleCalendarService  # Import the GoogleCalendarService class
from model_initializer import ModelInitializer
import google.generativeai as genai

class EventInitializer:
    def __init__(self):
        # Initialize the Google Calendar Service
        self.calendar_service = GoogleCalendarService()

        # Initialize the ModelInitializer for generating events using AI
        self.model_init = ModelInitializer(f"""
            You are a calendar assistant. Based on the following input, generate the required JSON for a Google Calendar event.
            The JSON should contain:
            - "summary": a short title for the event,
            - "start": the start time in ISO 8601 format,
            - "end": the end time in ISO 8601 format,
            - "timeZone": the time zone for the event.

            An example format is this:
            {{
                'summary': 'Meeting with John',
                'start': {{
                    'dateTime': '2024-10-18T10:00:00',
                    'timeZone': 'America/New_York',
                }},
                'end': {{
                    'dateTime': '2024-10-18T11:00:00',
                    'timeZone': 'America/New_York',
                }},
            }}
            """,
            config_mods={"response_mime_type": "application/json"}
        )

    # Use Gemini as the event generator
    async def event_init_ai_server(self, action):
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
        prompt = f"""
            {action}
            Right now it is {current_time} in UTC.
        """
        # Generate response
        response = self.model_init.model.generate_content(prompt)
        return response

    # Insert new event into Google Calendar
    def add_event(self, event_body):
        if not self.validate_event_body(event_body):
            return False  # Validate event body

        event = self.calendar_service.service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
        
        print('Event created:', event_body)
        webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar

    # Helper method to validate event specifications
    def validate_event_body(self, event_body):
        try:
            return event_body['summary'] and event_body['start'] and event_body['end']
        except KeyError:
            return False

    # Method to check if the scopes are correct
    def check_scopes(self):
        self.calendar_service.check_scopes()

# Testing
async def main():
    agent = EventInitializer()

    # Sample event for the next hour
    agent.add_event(event_body={
        'summary': 'Work on TimeSpace',
        'start': {
            'dateTime': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat(),
            'timeZone': 'America/New_York',
        },
    })

    # Schedule a meeting using Gemini AI
    event_body = json.loads((await agent.event_init_ai_server("Schedule a meeting tomorrow afternoon with Eric")).text)
    agent.add_event(event_body)

if __name__ == "__main__":
    asyncio.run(main())
