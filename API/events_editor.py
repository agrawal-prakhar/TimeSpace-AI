import webbrowser
import datetime
from gcal_service import GoogleCalendarService  # Import the existing GoogleCalendarService class
from model_initializer import ModelInitializer
import asyncio
import json

class EventEditor:
    def __init__(self):
        # Use the GoogleCalendarService to handle authentication and service initialization
        calendar_service = GoogleCalendarService()
        self.service = calendar_service.service

        # Initialize the AI model for event editing
        self.model_init = ModelInitializer(f"""
            You are a calendar assistant. You will receive instructions as provided by the user, a list of the user's events, and current datetime info.
            Pick the appropriate event and generate a new JSON for that event with changes reflecting the instructions from the user.
        """, config_mods={"response_mime_type": "application/json"})

    # Use the AI model to edit an event based on user input
    async def event_edit_ai_server(self, action, events):
        # Generate the prompt for the AI model
        prompt = f"""
            {action}
            {events}
            Right now it is {datetime.datetime.now(datetime.timezone.utc).isoformat()} in UTC.
        """
        # Generate response using the AI model
        response = self.model_init.model.generate_content(prompt)
        return response

    # Delete an event from Google Calendar by event ID
    def delete_event(self, event_body):
        try:
            event = self.service.events().delete(calendarId='primary', eventId=event_body['id']).execute()
            print('Event deleted:', event_body['summary'])
        except Exception as e:
            print(f"Error deleting event: {e}")

    # Update an event on Google Calendar by event ID
    def update_event(self, event_body):
        try:
            event = self.service.events().update(calendarId='primary', eventId=event_body['id'], body=event_body).execute()
            print('Event updated:', event_body['summary'])
        except Exception as e:
            print(f"Error updating event: {e}")

    # Get upcoming events from the user's Google Calendar
    def get_events(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=now.isoformat(),
                maxResults=10,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            return events
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []

# Testing
async def main():
    agent = EventEditor()

    # Fetch upcoming events
    events = agent.get_events()

    # Log fetched events for debugging
    print("Fetched Events:")
    print(json.dumps(events, indent=2))

    # Use AI to generate an updated event body
    ai_response = await agent.event_edit_ai_server("Change name of upcoming event to True", events)
    
    try:
        # Attempt to parse the AI-generated event body
        event_body = json.loads(ai_response.text)
        print("AI-Generated Event Body:")
        print(json.dumps(event_body, indent=2))
    except json.JSONDecodeError as e:
        print(f"Error decoding AI response: {e}")
        return

    # Handle the case where event_body is a list of events
    if isinstance(event_body, list):
        for single_event in event_body:
            # If the event is cancelled, delete it; otherwise, update the event
            if single_event.get('status') == 'cancelled':
                agent.delete_event(single_event)
            else:
                agent.update_event(single_event)
    elif isinstance(event_body, dict):
        # If a single event is returned as a dict, process it directly
        if event_body.get('status') == 'cancelled':
            agent.delete_event(event_body)
        else:
            agent.update_event(event_body)
    else:
        print(f"Unexpected event_body format: {type(event_body)}. Expected list or dict.")

if __name__ == "__main__":
    asyncio.run(main())