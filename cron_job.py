from apscheduler.schedulers.blocking import BlockingScheduler
from main import run_notion_gcal_sync


if __name__ == '__main__':
    # Create an instance of scheduler and add function.
    scheduler = BlockingScheduler()
    scheduler.add_job(run_notion_gcal_sync, 'interval', seconds=90)

    scheduler.start()
