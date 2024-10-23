from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from googleapiclient.errors import HttpError
from gcal_service import GoogleCalendarService

# Class to scrape Google Calendar (Gcal)
class GcalScraper:
    def __init__(self, calendar_service):
        """
        Initialize the GcalScraper with an instance of GoogleCalendarService.
        :param calendar_service: An instance of GoogleCalendarService.
        """
        self.service = calendar_service.service
        self.calendar_time_zone = self._fetch_primary_timezone()

    def _fetch_primary_timezone(self):
        """Fetch the primary calendar's timezone."""
        try:
            calendar = self.service.calendars().get(calendarId='primary').execute()
            return ZoneInfo(calendar['timeZone'])
        except HttpError as error:
            print(f"Error fetching primary calendar timezone: {error}")
            raise

    def get_events_on_date(self, event_date):
        """
        Get all events on a specific date from the primary calendar.

        :param event_date: A string date in 'YYYY-MM-DD' format.
        :return: A list of events on the given date.
        """
        event_date_dt = self._convert_to_datetime(event_date)
        event_end_dt = event_date_dt + timedelta(days=1) - timedelta(seconds=1)

        try:
            events = self.service.events().list(
                calendarId='primary',
                timeMin=event_date_dt.isoformat(),
                timeMax=event_end_dt.isoformat(),
                timeZone=self.calendar_time_zone.key
            ).execute()

            return events.get('items', [])
        except HttpError as error:
            print(f"Error fetching events: {error}")
            return []

    def get_busy_times(self, event_date):
        """
        Get the busy times (i.e., time ranges where events exist) on a specific date.

        :param event_date: A string date in 'YYYY-MM-DD' format.
        :return: A dictionary containing busy times for the specified date.
        """
        event_date_dt = self._convert_to_datetime(event_date)
        event_end_dt = event_date_dt + timedelta(days=1) - timedelta(seconds=1)

        body = {
            "timeMin": event_date_dt.isoformat(),
            "timeMax": event_end_dt.isoformat(),
            "timeZone": self.calendar_time_zone.key,
            "items": [{"id": 'primary'}]
        }

        try:
            events_result = self.service.freebusy().query(body=body).execute()
            return events_result.get('calendars', {})
        except HttpError as error:
            print(f"Error fetching busy times: {error}")
            return {}

    def _convert_to_datetime(self, date_string):
        """
        Helper function to convert a date string in 'YYYY-MM-DD' format to a timezone-aware datetime object.

        :param date_string: A string date in 'YYYY-MM-DD' format.
        :return: A timezone-aware datetime object.
        """
        dt = datetime.strptime(date_string, '%Y-%m-%d')
        return dt.replace(tzinfo=self.calendar_time_zone)

    # Placeholder for finding time slots (not yet implemented)
    def find_time(self, date, duration):
        """Find an available time slot on a specific date for the given duration."""
        pass

    # Placeholder for getting tasks (not yet implemented)
    def get_tasks(self):
        """Fetch tasks associated with calendar events."""
        pass


# Testing
if __name__ == "__main__":
    # Instantiate the GoogleCalendarService
    calendar_service = GoogleCalendarService()

    # Instantiate the GcalScraper using the authenticated calendar service
    cal_scraper = GcalScraper(calendar_service)
    
    # Get events on a specific date
    events = cal_scraper.get_events_on_date('2024-10-23')
    if events:
        for event in events:
            print("Event:", event.get('summary', 'No Title'))
            print("Start:", event['start'].get('dateTime', 'All-day event'))
            print("End:", event['end'].get('dateTime', 'All-day event'))
    else:
        print("No events found.")

    # Get busy times on a specific date
    busy_times = cal_scraper.get_busy_times('2024-10-20')
    for calendar_id, busy_info in busy_times.items():
        print(f"Calendar: {calendar_id}")
        print("Busy periods:", busy_info.get('busy', 'No busy periods'))
        print()
