import webbrowser
import datetime
import asyncio
import json
from gcal_service import GoogleCalendarService  # Import the GoogleCalendarService class
from model_initializer import ModelInitializer
import pytz
import textwrap

class EventInitializer:
    def __init__(self):
        # Initialize the Google Calendar Service
        calendar_service = GoogleCalendarService()
        self.service = calendar_service.service

        self.model_init = ModelInitializer(
            textwrap.dedent(f"""
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
            """),
            config_mods={"response_mime_type": "application/json"}
        )

    # Use Gemini as the event generator
    async def event_init_ai_server(self, action):

        current_time = datetime.datetime.now().isoformat() 
        user_timezone = pytz.timezone(pytz.country_timezones('US')[0])
        # Passing current local time and user's time zone into the prompt so that model has proper awareness

        prompt = textwrap.dedent(f"""
            {action}
            Right now it is {current_time} in {user_timezone}
        """)
        # Generate response
        response = self.model_init.model.generate_content(prompt)
        return response

    # Insert new event into Google Calendar
    def add_event(self, event_body):
        try:
            if self.validate_event_body(event_body):
                event = self.service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
                print('Event created: ', event_body)
                webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar UI
        except Exception as e:
            print(
                textwrap.dedent(f"""
                    {e}
                    Unexpected input format: {event_body}
                """)
            )

    # Testing method to check scopes 
    def check_scopes(self):
        print(self.service.calendarList().get(calendarId='primary').execute())
    
    # Handle response from AI
    def process_response(self, response):
        try:
            event_body = json.loads(response)
            self.add_event(event_body)
        except Exception as e:
            print(
                textwrap.dedent(f"""
                    {e}
                    Unexpected response format: {response}
                """)
            )
    
    # Invoke agent, handles action to generate and process response
    async def invoke(self, action):
        response = (await self.event_init_ai_server(action)).text
        self.process_response(response)


    # Helper method to validate event specifications
    # Needs work, doesn't give useful output or check type of input, also KeyError doesn't work as a catch all
    def validate_event_body(self, event_body):
        try:
            return event_body['summary'] and event_body['start'] and event_body['end']
        except Exception as e:
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
    await agent.invoke("Schedule me some time to do my math hw tomorrow.")

if __name__ == "__main__":
    asyncio.run(main())
