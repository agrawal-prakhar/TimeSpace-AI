import webbrowser
import datetime
import gcal_service as gcal
from model_initializer import ModelInitializer
import google.generativeai as genai
import asyncio
import json
import pytz

class EventInitializer:
    def __init__(self):
        self.service = gcal.get_service() # We should consider passing in service so as to avoid redundancy, declaring it at the higher level which also declares the agents

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

        prompt = f"""
            {action}
            Right now it is {datetime.datetime.now(datetime.UTC).isoformat() + "Z"} in {pytz.timezone(pytz.country_timezones('US')[0])}
            """
        # Generate response
        response = self.model_init.model.generate_content(prompt) # changed from chat_session.send_message because this agent doesn't require ongoing thread communication
        return response

    # IS IT MORE APPROPRIATE TO MAKE IT 'add_events' and pass in a set of events 

    # Insert new event into Google Calendar
    def add_event(self, event_body):
        if not validate_event_body(event_body):
            return False  # Validate event body
        
        event = self.service.events().insert(calendarId='primary', body=event_body).execute()  # Insert event
        
        print('Event created: ', event_body)
        webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar

    # Testing method to check scopes 
    def check_scopes(self):
        print(self.service.calendarList().get(calendarId='primary').execute())


# Helper method to validate event specifications
# Needs work, doesn't give useful output or check type of input, also KeyError doesn't work as a catch all
def validate_event_body(event_body):
    try:
        return event_body['summary'] and event_body['start'] and event_body['end']
    except KeyError:
        return False


# Testing
async def main():
    agent = EventInitializer()

    # Sample event for the next hour
    agent.add_event(event_body={
        'summary': 'Work on TimeSpace',
        'start': {
            'dateTime': datetime.datetime.now(datetime.UTC).isoformat(),
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': (datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)).isoformat(),
            'timeZone': 'America/New_York',
        },
    })

    # Schedule a meeting using Gemini AI
    event_body = json.loads((await agent.event_init_ai_server("Schedule a meeting tomorrow afternoon with Eric")).text) # Not sure if this is the best place to do that processing?
    # DEAL WITH INCOMPLETE INPUT/FOLLOW UP SYSTEM
    # IN GENERAL WE REALLY REALLY WANNA HAMMER THE LIMITATION OF LLMS TO NOT PROMPT FOR NECESSARY SUPPLEMENTARY INFO, AND ACT IRRADICALLY ON AN IMCOMPLETE PRETENSE
    agent.add_event(event_body)

if __name__ == "__main__":
    asyncio.run(main())
