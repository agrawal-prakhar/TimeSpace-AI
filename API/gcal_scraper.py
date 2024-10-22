
import webbrowser
from datetime import *
import gcal_service as gcal
from model_initializer import ModelInitializer
import google.generativeai as genai
import asyncio
import json
import pytz

#Class to scrape Gcal
class Gcal_Scraper:

    #initialize the service
    def __init__(self):
        self.service = gcal.get_service()
        calendar = self.service.calendars().get(calendarId='primary').execute()
        self.calendar_time_zone = calendar['timeZone']

    #get events on a specified day
    def get_events_at_date(self, event_date):

        split_date = event_date.split('-')

        event_date = datetime(int(split_date[0]), int(split_date[1]), int(split_date[2]), 00, 00, 00, 0)
        event_date = pytz.timezone(self.calendar_time_zone).localize(event_date).isoformat()

        end = datetime(int(split_date[0]), int(split_date[1]), int(split_date[2]), 23, 59, 59, 999999)
        end = pytz.timezone(self.calendar_time_zone).localize(end).isoformat()

        # 

        ''' @TODO Could iterate over the different page tokens like this if need be (for quering large sets of data)

        page_token = None
        while True:
            page_token = events.get('nextPageToken')
                if not page_token:
                    break

        '''
        events = self.service.events().list(calendarId='primary', timeMin = event_date, timeMax= end, timeZone=self.calendar_time_zone, pageToken=page_token).execute()

        return events['items']
    

    def get_busy_times(self, event_date):

        split_date = event_date.split('-')

        event_date = datetime(int(split_date[0]), int(split_date[1]), int(split_date[2]), 00, 00, 00, 0)
        event_date = pytz.timezone(self.calendar_time_zone).localize(event_date).isoformat()

        end = datetime(int(split_date[0]), int(split_date[1]), int(split_date[2]), 23, 59, 59, 999999)
        end = pytz.timezone(self.calendar_time_zone).localize(end).isoformat()


        body = {
            "timeMin": event_date,
            "timeMax": end,
            "timeZone": self.calendar_time_zone,
            "items": [

                {"id": 'primary' }
            ]
            
        }
        eventsResult = self.service.freebusy().query(body=body).execute()
        #print(eventsResult)
        cal_dict = eventsResult[u'calendars']

        return cal_dict
        
                

    #find a time based on the date and the duration of the new activity
    def find_time(self, date, duration):
        pass


    #get tasks of the events
    def get_tasks(self):
        pass

#Testing

async def main():

    cal_sraper = Gcal_Scraper()
    events = cal_sraper.get_events_at_date('2024-10-20')
    
    for event in events:
        print("Event", event)
        print("Start: ", event['start']['dateTime'])
        print("End: ", event['end']['dateTime'])
        print()

    busy_times = cal_sraper.get_busy_times('2024-10-20')
    for cal_name in busy_times:
            print(busy_times[cal_name])




if __name__ == "__main__":
    asyncio.run(main())

