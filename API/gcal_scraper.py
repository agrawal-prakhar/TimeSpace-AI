from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from googleapiclient.errors import HttpError
from gcal_service import GoogleCalendarService
from model_initializer import ModelInitializer
import textwrap
import pytz
import json
import asyncio

# Class to scrape Google Calendar (Gcal)
class GcalScraper:
    def __init__(self, calendar_service):
        """
        Initialize the GcalScraper with an instance of GoogleCalendarService.
        :param calendar_service: An instance of GoogleCalendarService.
        """
        self.service = calendar_service.service
        self.calendar_time_zone = self._fetch_primary_timezone() # Be careful, this gets the calendar
        self.model_init = ModelInitializer(
            textwrap.dedent(f"""
                You are an agent for a Google Calendar AI assistant. Your job is to craft query parameters that will list out the 'relevant' events based on the prompt, to supply context for the actions other agents. You will be given local time and the timezone of the user.
                The supported parameters, in accordance with the Google API documentation for Events: list, are as follows:
                - calendarId    string  Which of the user's calendars to sample. For primary calendar (default behavior) use the "primary" keyword REQUIRED PARAMETER.
                - eventTypes	string	Event types to return. Optional. This parameter can be repeated multiple times to return events of different types. If unset, returns all event types. 
                    Acceptable values are: 
                    - "birthday": Special all-day events with an annual recurrence.
                    - "default": Regular events.
                    - "focusTime": Focus time events.
                    - "fromGmail": Events from Gmail.
                    - "outOfOffice": Out of office events.
                    - "workingLocation": Working location events.
                - iCalUID	string	Specifies an event ID in the iCalendar format to be provided in the response. Optional. Use this if you want to search for an event by its iCalendar ID.
                - maxAttendees	integer	The maximum number of attendees to include in the response. If there are more than the specified number of attendees, only the participant is returned. Optional.
                - maxResults	integer	Maximum number of events returned on one result page. The number of events in the resulting page may be less than this value, or none at all, even if there are more events matching the query. Incomplete pages can be detected by a non-empty nextPageToken field in the response. By default the value is 250 events. The page size can never be larger than 2500 events. Optional.
                - orderBy	string	The order of the events returned in the result. Optional. The default is an unspecified, stable order.
                    Acceptable values are:
                        - "startTime": Order by the start date/time (ascending). This is only available when querying single events (i.e. the parameter singleEvents is True)
                        - "updated": Order by last modification time (ascending).
                - pageToken	string	Token specifying which result page to return. Optional.
                - privateExtendedProperty	string	Extended properties constraint specified as propertyName=value. Matches only private properties. This parameter might be repeated multiple times to return events that match all given constraints.
                - q	string	Free text search terms to find events that match these terms in the following fields:
                    - summary
                    - description
                    - location
                    - attendee's displayName
                    - attendee's email
                    - organizer's displayName
                    - organizer's email
                    - workingLocationProperties.officeLocation.buildingId
                    - workingLocationProperties.officeLocation.deskId
                    - workingLocationProperties.officeLocation.label
                    - workingLocationProperties.customLocation.label
                These search terms also match predefined keywords against all display title translations of working location, out-of-office, and focus-time events. For example, searching for "Office" or "Bureau" returns working location events of type officeLocation, whereas searching for "Out of office" or "Abwesend" returns out-of-office events. Optional.
                - sharedExtendedProperty	string	Extended properties constraint specified as propertyName=value. Matches only shared properties. This parameter might be repeated multiple times to return events that match all given constraints.
                - showDeleted	boolean	Whether to include deleted events (with status equals "cancelled") in the result. Cancelled instances of recurring events (but not the underlying recurring event) will still be included if showDeleted and singleEvents are both False. If showDeleted and singleEvents are both True, only single instances of deleted events (but not the underlying recurring events) are returned. Optional. The default is False.
                - showHiddenInvitations	boolean	Whether to include hidden invitations in the result. Optional. The default is False.
                - singleEvents	boolean	Whether to expand recurring events into instances and only return single one-off events and instances of recurring events, but not the underlying recurring events themselves. Optional. The default is False. (USE TRUE FOR OUR USE CASE)
                - timeMax	datetime	Upper bound (exclusive) for an event's start time to filter by. Optional. The default is not to filter by start time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. Milliseconds may be provided but are ignored. If timeMin is set, timeMax must be greater than timeMin.
                - timeMin	datetime	Lower bound (exclusive) for an event's end time to filter by. Optional. The default is not to filter by end time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. Milliseconds may be provided but are ignored. If timeMax is set, timeMin must be smaller than timeMax.
                - timeZone	string	Time zone used in the response. Optional. The default is the time zone of the calendar.
                - updatedMin	datetime	Lower bound for an event's last modification time (as a RFC3339 timestamp) to filter by. When specified, entries deleted since this time will always be included regardless of showDeleted. Optional. The default is not to filter by last modification time.
                
                Craft your query parameters logically, utilizing query parameters only when they are necessary to provide "relevant context" for the action. Here are some examples. For an action that mentions "editing the next upcoming event" you might set the timeMin to the current time and maxResults to 1, because all that matters is that one event. For the action that mentions "scheduling an event on Friday afternoon", you would want to fetch the existing events on Friday afternoon, and so set timeMin to 12:00PM that day and timeMax to 6:00pm that day.
                DEFAULT BEHAVIOR: Keep the query broad when unsure, so as to provide as much context as possible.
            """),
            config_mods={"response_mime_type": "application/json"}
        )
    
    # AI WORKFLOW 
    async def event_list_ai_server(self, action):

        current_time = datetime.now().isoformat() 
        user_timezone = pytz.timezone(pytz.country_timezones('US')[0])
        # Passing current local time and user's time zone into the prompt so that model has proper awareness

        prompt = textwrap.dedent(f"""
            {action}
            Right now it is {current_time} in {user_timezone}
        """)
        # Generate response
        response = self.model_init.model.generate_content(prompt)
        return response
    
    def process_response(self, response):
        try:
            query = json.loads(response)
            print("Query:", query)
            events_result = self.service.events().list(
                **query
            ).execute()
            events = events_result.get("items", [])
            return events
        except Exception as e:
            print(textwrap.dedent(f"""
                {e}
                Unexpected response format: {response}
            """))
            return []

    async def invoke(self, action):
        response = (await self.event_list_ai_server(action)).text
        return self.process_response(response)

    # DETERMINISTIC WORKFLOW
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


async def main():
    # Instantiate the GoogleCalendarService
    calendar_service = GoogleCalendarService()

    # Instantiate the GcalScraper using the authenticated calendar service
    cal_scraper = GcalScraper(calendar_service)

    events = await cal_scraper.invoke("Schedule me some time to do my Math hw this afternoon")
    print("\nEvents:", events, "\n")

    events = await cal_scraper.invoke("Delete all my events from the past 3 days")
    print("\nEvents:", events, "\n")


    
    # COMMENTED OUT FOR TESTING, BUT TOO MUCH PROCESSING FOR MAIN FUNCTION
    """ # Get events on a specific date
    events = cal_scraper.get_events_on_date('2024-10-23')
    if events:
        for event in events:
            print("Event:", event.get('summary', 'No Title'))
            print("Start:", event['start'].get('dateTime', 'All-day event'))
            print("End:", event['end'].get('dateTime', 'All-day event'))
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
        print()  """

# Testing
if __name__ == "__main__":
    asyncio.run(main())
