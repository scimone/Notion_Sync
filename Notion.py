import os
from notion_client import Client
from datetime import datetime, timedelta


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

    # def format_date(self, date):
    #     return date.strftime("%Y-%m-%d")

    def query(self, time_min, time_max):
        response = self.client.databases.query(
            **{
                "database_id": self.database_id,
                "filter": {
                    "and": [
                        {
                            "property": self.properties['Date'],
                            "date": {
                                "on_or_after": self.format_date(time_min)
                            }
                        },
                        {
                            "property": self.properties['Date'],
                            "date": {
                                "before": self.format_date(time_max)
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
            'gcal_ids': [],
            'last_updated': [],
            'needs_update': [],
            'notion_ids': []
        }

        for item in events:
            # need to test if the properties are specified for the item, otherwise error
            item_properties = item['properties'].keys()

            if self.properties['Category'] in item_properties:
                entries['categories'].append(item['properties'][self.properties['Category']]['select']['name'])
            else:
                entries['categories'].append(None)

            if item['properties'][self.properties['GCal ID']]['rich_text']:  # if not empty
                entries['gcal_ids'].append(item['properties'][self.properties['GCal ID']]['rich_text'][0]['text']['content'])
            else:
                entries['gcal_ids'].append(None)

            if self.properties['Duration'] in item_properties:
                entries['durations'].append(item['properties'][self.properties['Duration']]['number'])
            else:
                entries['durations'].append(None)

            if self.properties['Last Updated'] in item_properties:
                entries['last_updated'].append(self.parse_date(item['properties'][self.properties['Last Updated']]['date']['start']))
            else:
                entries['last_updated'].append(None)

            if self.properties['Last Edited'] > self.properties['Last Updated']:
                entries['needs_update'].append(True)
                print(item['properties'][self.properties['Name']]['title'][0]['text']['content'])
            else:
                entries['needs_update'].append(False)

            entries['names'].append(item['properties'][self.properties['Name']]['title'][0]['text']['content'])
            entries['start_dates'].append(self.parse_date(item['properties'][self.properties['Date']]['date']['start']))
            entries['end_dates'].append(self.parse_date(item['properties'][self.properties['Date']]['date']['end']))
            entries['notion_ids'].append(item['id'])

        return entries

    def format_date(self, date, timezone_appendix='+02:00'):  # TODO timezone stuff
        return date.strftime("%Y-%m-%dT%H:%M:%S" + timezone_appendix)

    def parse_date(self, date):
        if date:  # if not None
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S.%f%z']:
                try:
                    return datetime.strptime(date, fmt)
                except ValueError:
                    pass
        else:
            return None

    def add_entry(self, name, start_date=None, end_date=None, duration=None, gcal_id=None, category=None):
        data = {
            "parent": {
                "database_id": self.database_id,
            },
            "properties": {
                self.properties['Name']: {
                    "type": 'title',
                    "title": [
                        {
                            "type": 'text',
                            "text": {
                                "content": name
                            },
                        },
                    ],
                },
                self.properties['Last Updated']: {
                    "type": 'date',
                    'date': {
                        'start': self.format_date(datetime.now() - timedelta(hours=2), timezone_appendix='+00:00'),
                    }
                }
            }
        }

        if start_date:
            data['properties'][self.properties['Date']] = {}
            data['properties'][self.properties['Date']]['type'] = 'date'
            data['properties'][self.properties['Date']]['date'] = {'start': self.format_date(start_date)}

            if end_date:
                data['properties'][self.properties['Date']]['date']['end'] = self.format_date(end_date)

        if duration:
            data['properties'][self.properties['Duration']] = {}
            data['properties'][self.properties['Duration']]['type'] = 'number'
            data['properties'][self.properties['Duration']]['number'] = duration

        if gcal_id:
            data['properties'][self.properties['GCal ID']] = {}
            data['properties'][self.properties['GCal ID']]['type'] = 'rich_text'
            data['properties'][self.properties['GCal ID']]['rich_text'] = [{'text': {'content': gcal_id}}]

        if category:
            data['properties'][self.properties['Category']] = {}
            data['properties'][self.properties['Category']]['select'] = {'name': category}

        response = self.client.pages.create(**data)
        return response

    def update_entry(self, page_id, name=None, start_date=None, end_date=None, duration=None, gcal_id=None, category=None):
        data = {
            "page_id": page_id,
            "properties": {
                self.properties['Last Updated']: {
                    "type": 'date',
                    'date': {
                        'start': self.format_date(datetime.now() - timedelta(hours=2), timezone_appendix='+00:00'),  # TODO: timezone stuff
                    }
                }
            },
        }

        if name:
            # data['properties'][self.properties['Name']] = {}
            # data['properties'][self.properties['Name']]['type'] = 'title'
            # data['properties'][self.properties['Name']]['title'] = {'type': 'text', 'text': {}}
            # data['properties'][self.properties['Name']]['title']['text'] = {'content': name}

            data['properties'][self.properties['Name']] = {"type": 'title',
                                                            "title": [
                                                                {
                                                                    "type": 'text',
                                                                    "text": {
                                                                        "content": name
                                                                    },
                                                                },
                                                            ],
                                                           }

        if start_date and end_date:
            data['properties'][self.properties['Date']] = {}
            data['properties'][self.properties['Date']]['type'] = 'date'
            data['properties'][self.properties['Date']]['date'] = {'start': self.format_date(start_date),
                                                                   'end': self.format_date(end_date)}

        if duration:
            data['properties'][self.properties['Duration']] = {}
            data['properties'][self.properties['Duration']]['type'] = 'number'
            data['properties'][self.properties['Duration']]['number'] = duration

        if gcal_id:
            data['properties'][self.properties['GCal ID']] = {}
            data['properties'][self.properties['GCal ID']]['type'] = 'rich_text'
            data['properties'][self.properties['GCal ID']]['rich_text'] = [{'text': {'content': gcal_id}}]

        if category:
            data['properties'][self.properties['Category']] = {}
            data['properties'][self.properties['Category']]['select'] = {'name': category}

        response = self.client.pages.update(**data)
        return response


