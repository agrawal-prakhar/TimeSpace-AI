import webbrowser
import datetime
from gcal_service import GoogleCalendarService  # Import the existing GoogleCalendarService class
from model_initializer import ModelInitializer
import asyncio
import json
import textwrap
import pytz

class EventEditor:
    def __init__(self):
        # Use the GoogleCalendarService to handle authentication and service initialization
        calendar_service = GoogleCalendarService()
        self.service = calendar_service.service

        self.model_init = ModelInitializer( # dedent used to get rid of indentation
            textwrap.dedent(f"""
                You are a calendar assistant. You will recieve instructions as provided by the user, a list of the user's events, and current datetime info.
                Pick the appropriate event, and output a new JSON object for that event with changes reflecting the instructions from the user.
                IMPORTANT: IF THE USER INPUT IS AT ALL UNCLEAR, OR DOES NOT PERFECTLY MATCH UP TO AN EVENT FROM THE LIST, RETURN A JSON BRIEFLY DETAILING THE ERROR. This should be the DEFAULT behavior, i.e. most instruction possibilities should not match any event.
            """), # Currently configured for ONE output
            config_mods={"response_mime_type": "application/json"} # only mod to default config is output as JSON
        ) 
        # Declaring model with ModelInitializer class, consider having the class contain a method which RETURNS a model, rather than having to store an instance of model_init which contains its own model

    # Use the AI model to edit an event based on user input
    async def event_edit_ai_server(self, action, events):

        current_time = datetime.datetime.now().isoformat()  
        user_timezone = pytz.timezone(pytz.country_timezones('US')[0])
        # Passing current local time and user's timezone into the prompt so that model has proper awareness

        prompt = textwrap.dedent(f"""
            {action}
            {events}
            Right now it is {current_time} in {user_timezone}
        """)
        # Generate response
        response = self.model_init.model.generate_content(prompt) # simple generate_content here because agent doesn't require ongoing thread communication
        return response

    # Delete an event from Google Calendar by event ID
    def delete_event(self, event_body):
        try:
            event = self.service.events().delete(calendarId='primary', eventId=event_body['id']).execute()
            print('Event deleted:', event_body)
        except Exception as e:
            print(f"Error deleting event: {e}")

    # Update an event on Google Calendar by event ID
    def update_event(self, event_body):
        try:
            event = self.service.events().update(calendarId='primary', eventId=event_body['id'], body=event_body).execute()
            print('Event updated:', event_body)
            webbrowser.open(event.get('htmlLink'))  # Open event in Google Calendar UI
        except Exception as e:
            print(f"Error updating event: {e}")

    # Get upcoming events from the user's Google Calendar, TEMPORARY METHOD, FUNCTIONALITY WILL BE OUTSOURCED TO SCRAPER AGENT
    def get_events(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=(now + datetime.timedelta(days=0)).isoformat(), # change timedelta to test other timeframes
                maxResults=10,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            return events
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []
    
    # Given AI response, execute appropriate process
    def process_response(self, response):
        try:
            event_body = json.loads(response)
            if ('error' in event_body): # Currently, model is set up to return an error JSON if it can't find the right event, so this is handling that case
                print(response)
            else:
                self.delete_event(event_body) if event_body['status'] == 'cancelled' else self.update_event(event_body)
        except Exception as e: # If any error occurs (usually improper model output resulting in json.loads not being able to parse), print the error and the output
            print(
                textwrap.dedent(f"""
                    {e}
                    Unexpected response format, expected JSON: {response}
                """)
            )
    
    # Given action, execute full flow (getting events, querying agent, processing response)
    async def invoke(self, action):
        events = self.get_events()
        response = (await self.event_edit_ai_server(action, events)).text
        self.process_response(response)

# Testing
async def main():
    agent = EventEditor()

    await agent.invoke("Push my meeting with john back two hours")

if __name__ == "__main__":
    asyncio.run(main())