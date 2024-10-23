from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Standard in Python 3.9+
import gcal_service as gcal
import asyncio


# Class to scrape Google Calendar (Gcal)
class GcalScraper:
    def __init__(self):
        """Initialize the Google Calendar service and fetch the primary calendar time zone."""
        self.service = gcal.get_service()
        calendar = self.service.calendars().get(calendarId='primary').execute()
        self.calendar_time_zone = ZoneInfo(calendar['timeZone'])

    def get_events_on_date(self, event_date):
        """
        Get all events on a specific date from the primary calendar.

        :param event_date: A string date in 'YYYY-MM-DD' format.
        :return: A list of events on the given date.
        """
        event_date_dt = self._convert_to_datetime(event_date)
        event_end_dt = event_date_dt + timedelta(days=1) - timedelta(seconds=1)

        events = self.service.events().list(
            calendarId='primary',
            timeMin=event_date_dt.isoformat(),
            timeMax=event_end_dt.isoformat(),
            timeZone=self.calendar_time_zone.key  # Use the zone name (e.g., "America/New_York")
        ).execute()

        return events.get('items', [])

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

        events_result = self.service.freebusy().query(body=body).execute()
        return events_result.get('calendars', {})

    def _convert_to_datetime(self, date_string):
        """
        Helper function to convert a date string in 'YYYY-MM-DD' format to a timezone-aware datetime object.

        :param date_string: A string date in 'YYYY-MM-DD' format.
        :return: A timezone-aware datetime object.
        """
        dt = datetime.strptime(date_string, '%Y-%m-%d')
        return dt.replace(tzinfo=self.calendar_time_zone)

    # Future feature placeholders (not yet implemented)
    def find_time(self, date, duration):
        """Find an available time slot on a specific date for the given duration."""
        pass

    def get_tasks(self):
        """Fetch tasks associated with calendar events."""
        pass


# Testing
async def main():
    cal_scraper = GcalScraper()
    
    # Get events on a specific date
    events = cal_scraper.get_events_on_date('2024-10-20')
    for event in events:
        print("Event:", event.get('summary', 'No Title'))
        print("Start:", event['start'].get('dateTime', 'All-day event'))
        print("End:", event['end'].get('dateTime', 'All-day event'))
        print()

    # Get busy times on a specific date
    busy_times = cal_scraper.get_busy_times('2024-10-20')
    for calendar_id, busy_info in busy_times.items():
        print(f"Calendar: {calendar_id}")
        print("Busy periods:", busy_info.get('busy', 'No busy periods'))
        print()


if __name__ == "__main__":
    asyncio.run(main())
