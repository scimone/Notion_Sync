from apscheduler.schedulers.blocking import BlockingScheduler
from Main import run_sync


if __name__ == '__main__':
    # Create an instance of scheduler and add function.
    scheduler = BlockingScheduler()
    scheduler.add_job(run_sync, 'interval', seconds=90)

    scheduler.start()
