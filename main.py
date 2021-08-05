import config
from APIs import NotionAPI, GCalAPI
from datetime import datetime, timedelta, date
from config import notion_config, gcal_config

if __name__ == '__main__':
    today = datetime.today().strftime("%Y-%m-%d")
    gcal = GCalAPI(gcal_config)
    notion = NotionAPI(notion_config)
