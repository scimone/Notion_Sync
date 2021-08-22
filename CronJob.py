from apscheduler.schedulers.blocking import BlockingScheduler
from config import notion_config, gcal_config, timezone, todoist_token, sync_gcal, sync_todoist
from Main import run_sync, create_notion_api, create_todoist_api, create_gcal_api


if __name__ == '__main__':
    notion = create_notion_api()

    if sync_todoist and sync_gcal:
        todoist = create_todoist_api()
        gcal = create_gcal_api()
    elif sync_todoist:
        todoist = create_todoist_api()
        gcal = None
    elif sync_gcal:
        gcal = create_gcal_api()
        todoist = None
    else:
        todoist = None
        gcal = None

    args = [notion, todoist, gcal]

    # Create an instance of scheduler and add function.
    scheduler = BlockingScheduler()
    scheduler.add_job(run_sync, 'interval', seconds=30, args=args)

    scheduler.start()
