from apscheduler.schedulers.blocking import BlockingScheduler
from Todoist import TodoIstAPI
from Notion import NotionAPI
from Gcal import GCalAPI
import json
import os
from Main import run_sync


def create_notion_api():
    notion_config = json.loads(os.environ['notion_config'])
    notion = NotionAPI(os.environ['tz'], notion_config)
    return notion

def create_todoist_api():
    todoist = TodoIstAPI(os.environ['TODOIST_TOKEN'])
    return todoist

def create_gcal_api():
    gcal_config = json.loads(os.environ['gcal_config'])
    gcal = GCalAPI(os.environ['tz'], gcal_config)
    return gcal


if __name__ == '__main__':
    notion = create_notion_api()

    if os.environ['SYNC_TODOIST'] == "True" and os.environ['SYNC_GCAL'] == "True":
        todoist = create_todoist_api()
        gcal = create_gcal_api()
        args = [notion, todoist, gcal]
    elif os.environ['SYNC_TODOIST'] == "True":
        todoist = create_todoist_api()
        args = [notion, todoist, None]
    elif os.environ['SYNC_GCAL'] == "True":
        gcal = create_gcal_api()
        args = [notion, None, gcal]

    # Create an instance of scheduler and add function.
    scheduler = BlockingScheduler()
    scheduler.add_job(run_sync, 'interval', seconds=90, args=args)

    scheduler.start()
