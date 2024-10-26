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
        Get the busy times (i.e., time ranges where events exist) on a specific date for the primary calendar.

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
            return events_result.get('calendars', {})['primary']['busy']
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
    
    def parse_times(self, times):
        """
        Helper function to parse time blocks and return a list of start and end times in datetime format.

        :param times (dict): Dictionary containing time periods with 'start' and 'end' times in ISO 8601 format.
                                  Example structure: [{'start': 'ISO format', 'end': 'ISO format'}, ...]

        :return times_converted (list): List of tuples where each tuple contains the start and end times as datetime objects.
        """

        times_converted = []
        for time_block in times:
            start_time = datetime.fromisoformat(time_block['start'])
            end_time = datetime.fromisoformat(time_block['end'])
            times_converted.append((start_time, end_time))
        
        return times_converted
    
    def format_times(self, times):
        """
        Helper function to format time slots into a list of dictionaries with ISO format strings.

        :param times (list): List of tuples with start and end times for all different time slots.

        :return formatted_times (list): List of dictionaries representing time slots with 'start' and 'end' keys.
        """

        formatted_times = []
        for start, end in times:
            formatted_times.append({
                'start': start.isoformat(),
                'end': end.isoformat()
            })

        return formatted_times
        
    def find_times(self, date, duration, start_time = 7.0, end_time = 22.0):
        """
        Finds and returns all available time slots on a specific date for the given duration, excluding busy periods, for the primary calendar.

        :param date: A string representing the date (in 'YYYY-MM-DD' format) for which free times are to be found.
        :param duration: An integer representing the desired duration of the meeting in minutes.
        :param start_time: A float that represents the time at which your working day starts (time when you wake up) in millitary time. 7:30 would be represented as 7.5. Default: 7am.
        :param end_time: A float that represents the time at which your working day ends (time when you sleep) in millitary time. Default: 10pm.

        :return formatted_free_times (list): A list of available time slots, formatted and sorted, each represented 
                                            as a tuple containing start and end times in datetime format.
        """

        #Get all the busy times on a given date
        busy_times_raw = self.get_busy_times(date)
        busy_times = self.parse_times(busy_times_raw)
        date = self._convert_to_datetime(date)
        
        # Sort busy times by start time
        busy_times.sort(key=lambda x: x[0])

        #Get the exact hour and minutes from start and end times
        start_hour = int(start_time)
        start_minute = int((start_time - start_hour) * 60)

        end_hour = int(end_time)
        end_minute = int((end_time - end_hour) * 60)

        # Define the working day time range (Default 7am - 10pm)
        work_start_time = date.replace(hour= start_hour, minute=start_minute, second=0, microsecond=0)
        work_end_time = date.replace(hour= end_hour, minute=end_minute, second=0, microsecond=0)
        
        # Convert the duration to a timedelta object
        duration_delta = timedelta(minutes=duration)
        
        available_times = []
        current_time = work_start_time

        # Loop through busy times and find available gaps
        for busy_start, busy_end in busy_times:
            # Check if there is a gap between the current time and the next busy period
            if busy_start > current_time:
                gap = busy_start - current_time
                # If the gap is larger than or equal to the duration, it's an available slot
                if gap >= duration_delta:
                    available_times.append((current_time, busy_start))

            # Move the current time to the end of the busy period
            current_time = max(current_time, busy_end)

        # Check for availability between the end of the last busy period and the end of the workday
        if work_end_time > current_time:
            gap = work_end_time - current_time
            if gap >= duration_delta:
                available_times.append((current_time, work_end_time))

        # Format the free times to be helpful later
        formatted_free_times = self.format_times(available_times)
        
        # Return the formatted free times
        return formatted_free_times

# Testing
if __name__ == "__main__":
    # Instantiate the GoogleCalendarService
    calendar_service = GoogleCalendarService()

    # Instantiate the GcalScraper using the authenticated calendar service
    cal_scraper = GcalScraper(calendar_service)
    
    # Get events on a specific date
    events = cal_scraper.get_events_on_date('2024-10-20')
    if events:
        for event in events:
            print("Event:", event.get('summary', 'No Title'))
            print("Start:", event['start'].get('dateTime', 'All-day event'))
            print("End:", event['end'].get('dateTime', 'All-day event'))
            print()
    else:
        print("No events found.")

    # Get busy times on a specific date
    busy_times = cal_scraper.get_busy_times('2024-10-24')
    print(busy_times)

    print("Busy times: ")
    for time_slot in busy_times:
        start_time = time_slot['start']
        end_time = time_slot['end']
        print(f"Start: {start_time}")
        print(f"End: {end_time}")
        print() 

    #Find time slots available for atleast an hour on a specifc date for between specific times
    free_times = cal_scraper.find_times('2024-10-24', 60, 7.5, 23)
    print(free_times)

    print("Free times: ")
    for time_slot in free_times:
        start_time = time_slot['start']
        end_time = time_slot['end']
        print(f"Start: {start_time}")
        print(f"End: {end_time}")
        print() 
