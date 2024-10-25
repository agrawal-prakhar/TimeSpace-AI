import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scope for Google Tasks API
SCOPES = ["https://www.googleapis.com/auth/tasks"]

# Class to manage Google Tasks service and tasks
class GoogleTasksService:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    # Authenticate and get the Google Tasks service
    def authenticate(self):
        """Authenticates the user and initializes the Google Tasks API service."""
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
            self.service = build("tasks", "v1", credentials=self.creds)
        except HttpError as error:
            print(f"An error occurred: {error}")

    # Fetch tasks from the user's task list
    def get_tasks(self, tasklist_id='@default'):
        """Fetch tasks from the user's specified task list. Defaults to the primary task list."""
        try:
            results = self.service.tasks().list(tasklist=tasklist_id).execute()
            tasks = results.get('items', [])
            return tasks
        except HttpError as error:
            print(f"An error occurred while fetching tasks: {error}")
            return []

    # Print tasks in a formatted way
    def print_tasks(self, tasks):
        """Prints tasks in a human-readable format."""
        if not tasks:
            print("No tasks found.")
            return

        for task in tasks:
            title = task.get('title', 'No Title')
            due = task.get('due', 'No Due Date')
            status = task.get('status', 'No Status')
            print(f"Task: {title} | Due: {due} | Status: {status}")

# Testing the class
if __name__ == "__main__":
    tasks_service = GoogleTasksService()
    tasks = tasks_service.get_tasks()  # Fetch tasks from the default task list
    tasks_service.print_tasks(tasks)   # Print fetched tasks
