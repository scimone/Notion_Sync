import os
from notion_client import Client
from datetime import datetime


class NotionAPI():
    def __init__(self, notion_config):
        self.api_key = notion_config['API Key']
        self.database_id = notion_config['Database ID']
        self.properties = notion_config['Properties']
        self.client = self.setup_client()

    def setup_client(self):
        os.environ['NOTION_TOKEN'] = self.api_key
        client = Client(auth=os.environ['NOTION_TOKEN'])
        return client

    def format_date(self, date):
        return date.strftime("%Y-%m-%d")

    def query(self, today):
        response = self.client.databases.query(
            **{
                "database_id": self.database_id,
                "filter": {
                    "or": [
                        {
                            "property": self.properties['Date'],
                            "date": {
                                "equals": self.format_date(today)
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
        results = self._convert_query_results(response['results'])
        return results

    def _convert_query_results(self, events):
        entries = {
            'names': [],
            'start_dates': [],
            'end_dates': [],
            'categories': [],
            'durations': [],
            'event_ids': [],
            'last_updated': [],
            'needs_update': []
        }

        for item in events:
            # need to test if the properties are specified for the item, otherwise error
            item_properties = item['properties'].keys()

            if self.properties['Category'] in item_properties:
                entries['categories'].append(item['properties'][self.properties['Category']]['select']['name'])
            else:
                entries['categories'].append(None)

            if item['properties'][self.properties['Event ID']]['rich_text']:  # if not empty
                entries['event_ids'].append(item['properties'][self.properties['Event ID']]['rich_text'][0]['text']['content'])
            else:
                entries['event_ids'].append(None)

            if self.properties['Duration'] in item_properties:
                entries['durations'].append(item['properties'][self.properties['Duration']]['number'])
            else:
                entries['durations'].append(None)

            if self.properties['Last Updated'] in item_properties:
                entries['last_updated'].append(self.parse_date(item['properties'][self.properties['Last Updated']]['date']['start']))
            else:
                entries['last_updated'].append(None)

            entries['names'].append(item['properties'][self.properties['Name']]['title'][0]['text']['content'])
            entries['start_dates'].append(self.parse_date(item['properties'][self.properties['Date']]['date']['start']))
            entries['end_dates'].append(self.parse_date(item['properties'][self.properties['Date']]['date']['end']))
            entries['needs_update'].append(item['properties'][self.properties['Needs Update?']]['formula']['boolean'])

        return entries

    def parse_date(self, date):
        if date:  # if not None
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S.%f%z']:
                try:
                    return datetime.strptime(date, fmt)
                except ValueError:
                    pass
        else:
            return None

    def new_entry(self):
        pass

    def update_entry(self):
        pass


