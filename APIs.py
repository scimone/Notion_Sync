import os
from notion_client import Client
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
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
                                "next_week": {}
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
        self.client = self.setup_gcal_client()

    def setup_gcal_client(self):
        if not os.path.isfile("token.pkl"):
            self.renew_gcal_token()
        service = self.setup_gcal_service()

        try:
            client = service.calendars().get(calendarId=self.calendars[self.default_calendar]).execute()
        except:
            # refresh the service
            self.renew_gcal_token()
            service = self.setup_gcal_service()
            client = service.calendars().get(calendarId=self.calendars[self.default_calendar]).execute()
            # TODO: no idea which client I need
        return client

    def setup_gcal_service(self):
        credentials = pickle.load(open("token.pkl", "rb"))
        service = build("calendar", "v3", credentials=credentials)
        return service

    def renew_gcal_token(self):
        scopes = ['https://www.googleapis.com/auth/calendar']
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=scopes)
        credentials = flow.run_console()
        pickle.dump(credentials, open("token.pkl", "wb"))
