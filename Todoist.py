from todoist.api import TodoistAPI
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

    def get_labels(self):
        return 0

    def get_uncompleted_tasks(self):
        pass

    def check_item(self):
        pass

    def update_item(self):
        pass