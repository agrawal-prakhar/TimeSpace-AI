import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scope for Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Class to manage Google Calendar service and events
class GoogleCalendarService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    # Authenticate and get the Google Calendar service
    def authenticate(self):
        """Authenticates the user and initializes the Google Calendar API service."""
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If credentials are invalid or not present, prompt user for login
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open("token.json", "w") as token:
                token.write(self.creds.to_json())

        try:
            self.service = build("calendar", "v3", credentials=self.creds)
        except HttpError as error:
            print(f"An error occurred: {error}")


# Testing the class
if __name__ == "__main__":
    calendar_service = GoogleCalendarService()
    events = calendar_service.get_upcoming_events()
    calendar_service.print_events(events)
