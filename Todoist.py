from todoist.api import TodoistAPI
from datetime import datetime, timedelta
from config import todoist_token


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
        # entries = self._convert_entries(tasks)
        return tasks

    # def _get_all_tasks(self):
    #     tasks = self.api.state['items']
    #     return tasks
    #
    # def _get_updated_tasks(self, updates):
    #     tasks = updates['items']
    #     return tasks

    # def _convert_entries(self, items):
    #     labels = self.get_labels()
    #     entries = {
    #         'names': [],
    #         'start_dates': [],
    #         'priorities': [],
    #         'labels': [],
    #         'needs_update': [],
    #         'todoist_ids': [],
    #         'notion_ids': []
    #     }
    #
    #     for item in items:
    #         if item['checked'] == 1 and item['is_deleted'] == 0:
    #             entries['names'].append(item['content'])
    #             entries['ids'].append(item['ids'])
    #
    #     return entries

    def parse_date(self, date):
        if len(date) > 10:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')  # TODO: convert to timezone
        else:
            default_event_start = 8  # TODO: config var
            date = datetime.strptime(date, '%Y-%m-%d') + timedelta(hours=default_event_start)
        return date

    def get_labels(self, label_ids):
        label_dict = dict((label['id'], label['name']) for label in self.api.state['labels'])
        return [label_dict[label_id] for label_id in label_ids]

    def get_priority(self, priority):
        priority_dict = dict(zip(list(range(1, 5)), list(range(4, 0, -1))))
        return str(priority_dict[priority])

    def get_duration(self, priority):
        duration_dict = {
            '1': 3,
            '2': 0.75,
            '3': 0.25,
            '4': 1  # TODO: set to default length
        }
        return duration_dict[priority]

    def get_task_properties(self, task, name=False, task_id=False, done=False, labels=False, priority=False, date=False):
        properties = {}
        if name:
            properties['name'] = task['content']
        if task_id:
            properties['id'] = str(task['id'])
        if done:
            properties['done'] = bool(task['checked'])
        if labels:
            properties['labels'] = self.get_labels(task['labels'])
        if priority:
            properties['priority'] = self.get_priority(task['priority'])
        if date:
            properties['start_date'] = self.parse_date(task['due']['date'])
            properties['duration'] = self.get_duration(properties['priority'])
            properties['end_date'] = properties['start_date'] + timedelta(hours=properties['duration'])
        return properties

    def get_uncompleted_tasks(self):
        pass

    def check_item(self):
        pass

    def update_item(self):
        pass