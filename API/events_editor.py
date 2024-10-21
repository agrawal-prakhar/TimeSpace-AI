import webbrowser
import datetime
import gcal_service as gcal
from model_initializer import ModelInitializer
import google.generativeai as genai
import asyncio
import json
import pytz

class EventEditor:
    def __init__(self):
        self.service = gcal.get_service()

        self.model_init = ModelInitializer(f"""
            You are a calendar assistant. You will recieve instructions as provided by the user, a list of the user's events, and current datetime info. 
            Pick the appropriate event, and generate a new JSON for that event with changes reflecting the instructions from the user.
            """, # Could need further prompting, WE NEEEEEEED TO FIGURE OUT IF IT CAN'T FIND IT OR NOT ENOUGH INFO GIVEN
            config_mods={"response_mime_type": "application/json"}
        )

    # Use Gemini as the event generator
    async def event_edit_ai_server(self, action, events):

        prompt = f"""
            {action}
            {events}
            Right now it is {datetime.datetime.now(datetime.UTC).isoformat() + "Z"} in {pytz.timezone(pytz.country_timezones('US')[0])}
            """
        # Generate response
        response = self.model_init.model.generate_content(prompt) # changed from chat_session.send_message because this agent doesn't require ongoing thread communication
        return response


    #  Delete event from Google Calendar by ID
    def delete_event(self, event_body):
        
        event = self.service.events().delete(calendarId='primary', eventId=event_body['id']).execute()  # Delete event
        
        print('Event deleted: ', event)
    
    def update_event(self, event_body):
        
        event = self.service.events().update(calendarId='primary', eventId=event_body['id'], body=event_body).execute()

        print('Event updated: ', event)

# One reason I'm in favor of checking out Gemini function calling is that we could potentially use it to optimize the search for events, but making multiple API calls might be even slower than just a super general search.
# However the model could do a lot worse correctly choosing between a set of 50 events than 10.... also could be faster digesting 2 smaller prompts than 1 big one...

    def get_events(self):
        now = datetime.datetime.now(datetime.UTC)
        events_result = (
            self.service.events()
            .list(
                
                calendarId="primary",
                timeMin=now.isoformat(), # now + datetime.timedelta(days=-7) for last week
                maxResults=10, 
                singleEvents=True, # weird thing happening here, wont get future events if it's false?
            )
            .execute()
        )
        events = events_result.get("items", [])
        return events

# Testing
async def main():
    agent = EventEditor()

    events = agent.get_events()

    event_body = json.loads((await agent.event_edit_ai_server("Change name of upcoming event to True", events)).text)

    agent.delete_event(event_body) if event_body['status'] == 'cancelled' else agent.update_event(event_body)

if __name__ == "__main__":
    asyncio.run(main())
