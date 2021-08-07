import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
import pickle


class GCalAPI():
    def __init__(self, gcal_config):
        self.default_calendar = gcal_config['Default Calendar']
        self.default_event_start = gcal_config['Default Event Start']
        self.default_event_length = gcal_config['Default Event Length']
        self.calendar_ids = gcal_config['Calendars']
        self.calendars = {v: k for k, v in self.calendar_ids.items()}  # reverse dictionary
        self.service = self.setup_service()

    def setup_service(self):
        credentials = self.get_credentials()
        service = build("calendar", "v3", credentials=credentials)
        return service

    def get_credentials(self):
        if os.path.isfile("token.pkl"):
            credentials = self._load_credentials()
        else:
            credentials = None

        if not (credentials and credentials.valid):
            if credentials:
                credentials.refresh(Request())  # refresh credentials
            else:
                credentials = self._setup_credentials()
            self._save_credentials(credentials)

        return credentials

    def _setup_credentials(self):
        scopes = ['https://www.googleapis.com/auth/calendar']
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes=scopes)
        credentials = flow.run_local_server(port=0)
        return credentials

    def _save_credentials(self, credentials):
        pickle.dump(credentials, open("token.pkl", "wb"))

    def _load_credentials(self):
        credentials = pickle.load(open("token.pkl", "rb"))
        return credentials

    def query(self, time_min, time_max):
        results = []
        for calendar in list(self.calendar_ids.keys()):
            response = self.service.events().list(
                calendarId=self.calendar_ids[calendar],
                singleEvents=True,
                orderBy='updated',
                timeMin=self.format_date(time_min),
                timeMax=self.format_date(time_max)
            ).execute()
            results.extend(response.get('items', []))
        return self._convert_query_results(results)

    def _convert_query_results(self, results):

        entries = {
            'names': [],
            'start_dates': [],
            'end_dates': [],
            'calendars': [],
            'durations': [],
            'gcal_ids': [],
            'last_updated': [],
        }

        for item in results:
            # get dates
            start_date = self.parse_date(item['start'])
            end_date = self.parse_date(item['end'])
            if (start_date == end_date - timedelta(days=1)) and (start_date.hour == 0) and (start_date.minute == 0):  # one-day events
                start_date += timedelta(hours=self.default_event_start)
                end_date = start_date + timedelta(minutes=self.default_event_length)
            elif end_date > start_date + timedelta(days=1):  # all-day events over multiple days
                end_date -= timedelta(days=1)  # subtract one day because notion is weird and adds one day

            # append entries
            entries['names'].append(item['summary'])
            entries['start_dates'].append(start_date)
            entries['end_dates'].append(end_date)
            entries['durations'].append((end_date - start_date).seconds / 3600)
            entries['calendars'].append(self.calendars[item['organizer']['email']])
            entries['gcal_ids'].append(item['id'])
            entries['last_updated'].append(self.datetime_floor(self.parse_date(item['updated'])))
        return entries

    def format_date(self, date):
        timezone_appendix = '+02:00'  # TODO: centralize
        return date.strftime("%Y-%m-%dT%H:%M:%S") + timezone_appendix  # Change the last 5 characters to be representative of your timezone
        # ^^ has to be adjusted for when daylight savings is different if your area observes it

    def parse_date(self, date):
        if type(date) is dict:
            if 'dateTime' in date:
                date = datetime.strptime(date['dateTime'], '%Y-%m-%dT%H:%M:%S%z')  # TODO: other formats?
            elif 'date' in date:
                date = datetime.strptime(date['date'], '%Y-%m-%d')
        else:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f%z')
        return date

    def datetime_floor(self, dt):
        dt_floor = dt - timedelta(seconds=dt.second, microseconds=dt.microsecond)
        return dt_floor

    def add_entry(self, calendar, name, timezone, start_date, end_date, description=None, source=None):
        data = {
            'summary': name,
            'start': {
                'dateTime': self.format_date(start_date),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': self.format_date(end_date),
                'timeZone': timezone,
            },
        }

        if description:
            data['description'] = description
        if source:
            data['source'] = {
                'title': source['title'],
                'url': source['url'],
            }

        response = self.service.events().insert(calendarId=self.calendar_ids[calendar], body=data).execute()
        return response['id']


    def update_entry(self):
        pass