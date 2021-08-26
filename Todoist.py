from todoist.api import TodoistAPI
from datetime import datetime, timedelta
import pytz
from config import DEFAULT_EVENT_START, DEFAULT_EVENT_LENGTH


class TodoIstAPI():

    def __init__(self, todoist_token):
        self.api = TodoistAPI(todoist_token)
        self.api.sync();
        self.first_run = True

    def get_tasks(self):
        updates = self.api.sync()
        if self.first_run:
            tasks = self.api.state['items']  # get all tasks that are not deleted or checked
            self.first_run = False
        else:
            tasks = updates['items']  # only get updated tasks
        return tasks

    def parse_date(self, date):
        if len(date) > 20:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
        elif len(date) == 19:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        elif len(date) == 20:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        else:
            date = datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=DEFAULT_EVENT_START)
        return date

    def format_date(self, date, timezone=None):
        if type(date) is not datetime:
            date = datetime(date.year, date.month, date.day)
        if (date.tzinfo is None or date.tzinfo.utcoffset(date) is None) and timezone:
            tz = pytz.timezone(timezone)
            date = tz.localize(date)
        return date.strftime("%Y-%m-%dT%H:%M:%S")

    def get_labels(self, labels, todoist_format=False):
        if labels:
            if todoist_format:
                label_dict = dict((label['name'], label['id']) for label in self.api.state['labels'])
                labels = [label_dict[label] for label in labels]
            else:
                label_dict = dict((label['id'], label['name']) for label in self.api.state['labels'])
                labels = [label_dict[label] for label in labels]
        else:
            labels = None
        return labels

    def get_priority(self, priority, todoist_format=False):
        if priority:
            if todoist_format:
                priority_dict = dict(zip([str(i) for i in range(1,5)], list(range(4, 0, -1))))
            else:
                priority_dict = dict(zip(list(range(4, 0, -1)), [str(i) for i in range(1, 5)]))
            return priority_dict[priority]
        else:
            return None

    def get_duration(self, priority):
        duration_dict = {
            '1': 3,
            '2': 0.75,
            '3': 0.25,
            '4': DEFAULT_EVENT_LENGTH
        }
        return duration_dict[priority]

    def get_task_properties(self, task, duration=None):
        properties = {'name': task['content'], 'id': str(task['id']), 'done': bool(task['checked'])}

        if 'labels' in task.data.keys():
            properties['labels'] = self.get_labels(task['labels'])
        else:
            properties['labels'] = None
        if 'priority' in task.data.keys():
            properties['priority'] = self.get_priority(task['priority'])
        else:
            properties['priority'] = None

        if task['due']:
            properties['start_date'] = self.parse_date(task['due']['date'])
            if not duration:
                if properties['priority']:
                    duration = self.get_duration(properties['priority'])
                else:
                    duration = DEFAULT_EVENT_LENGTH
            properties['end_date'] = properties['start_date'] + timedelta(hours=duration)
            properties['duration'] = duration
        else:
            properties['start_date'] = None
            properties['end_date'] = None
            properties['duration'] = None
        return properties

    def check_or_uncheck_item(self, todoist_id, done):
        item = self.api.items.get_by_id(todoist_id)
        if done:
            item.complete()
        else:
            item.uncomplete()

    def delete_item(self, todoist_id, delete):
        item = self.api.items.get_by_id(todoist_id)
        if delete:
            item.delete()

    def add_entry(self, name, start_date=None, priority=None, parent_id=None, labels=None):
        data = {
            "content": name
        }
        if start_date:
            data["due"] = {}
            data["due"]["date"] = self.format_date(start_date)
        if priority and priority != []:
            data["priority"] = priority
        if parent_id:
            data["parent_id"] = parent_id
        if labels and labels != []:
            data["labels"] = labels

        item = self.api.items.add(**data)
        todoist_id = item["id"]

        return todoist_id

    def update_entry(self, todoist_id, name=None, start_date=None, priority=None, parent_id=None, labels=None):
        data = {}
        if name:
            data["content"] = name
        if start_date:
            data["due"] = {}
            data["due"]["date"] = self.format_date(start_date)
        if priority and priority != []:
            data["priority"] = priority
        if parent_id:
            data["parent_id"] = parent_id
        if labels and labels != []:
            data["labels"] = labels
        item = self.api.items.get_by_id(todoist_id)
        item.update(**data)