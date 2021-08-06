from Notion import NotionAPI
from Gcal import GCalAPI
from config import notion_config, gcal_config
from datetime import datetime, timedelta


if __name__ == '__main__':
    today = datetime.now()

    # set up APIs
    gcal = GCalAPI(gcal_config)
    notion = NotionAPI(notion_config)

    # get all entries from today to next month

    time_min = today
    time_max = today + timedelta(days=30)

    # gcal
    gcal_entries = gcal.query(time_min, time_max)
    print(gcal_entries)

    # notion
    notion_entries = notion.query(today)
    print(notion_entries)

