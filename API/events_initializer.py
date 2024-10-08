import webbrowser
import datetime

import gcal_scraping_quickstart as gcal;

class EventInitializer:
    
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
    try:
        return event_body['summary'] and event_body['start'] and event_body['end']
    finally:
        return False

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
  