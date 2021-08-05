import os
from notion_client import Client
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle


class NotionAPI():
    def __init__(self, notion_config):
        self.api_key = notion_config['API Key']
        self.database_id = notion_config['Database ID']
        self.properties = notion_config['Database Properties']
        self.client = self.setup_client()

    def setup_client(self):
        os.environ['NOTION_TOKEN'] = self.api_key
        client = Client(auth=os.environ['NOTION_TOKEN'])
        return client

    def query(self, today):
        response = self.client.databases.query(  # this query will return a dictionary that we will parse for information that we want
            **{
                "database_id": self.database_id,
                "filter": {
                    "or": [
                        {
                            "property": self.properties['Date'],
                            "date": {
                                "equals": today
                            }
                        },
                        {
                            "property": self.properties['Date'],
                            "date": {
                                "next_month": {}
                            }
                        }
                    ]
                },
            }
        )
        results = response['results']
        return results

    def new_entry(self):
        pass

    def update_entry(self):
        pass


class GCalAPI():
    def __init__(self, gcal_config):
        self.default_calendar = gcal_config['Name of Default Calendar']
        self.default_event_start = gcal_config['Default Event Start']
        self.default_event_length = gcal_config['Default Event Length']
        self.calendars = gcal_config['Calendars']
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

    def query(self, calendar_id, time_min, time_max):
        response = self.service.events().list(
            calendarId=calendar_id,
            singleEvents=True,
            orderBy='updated',
            timeMin=self.format_date(time_min),
            timeMax=self.format_date(time_max)
        ).execute()
        return response

    def format_date(self, date):
        timezone_appendix = '+02:00'
        return date.strftime("%Y-%m-%dT%H:%M:%S") + timezone_appendix  # Change the last 5 characters to be representative of your timezone
        # ^^ has to be adjusted for when daylight savings is different if your area observes it
