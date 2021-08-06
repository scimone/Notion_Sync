from Notion import NotionAPI
from Gcal import GCalAPI
from config import notion_config, gcal_config
from datetime import datetime, timedelta, date
import numpy as np

if __name__ == '__main__':
    # set up APIs

    gcal = GCalAPI(gcal_config)
    notion = NotionAPI(notion_config)

    # get all entries from today to next month

    today = date.today()
    time_min = today - timedelta(seconds=1)
    time_max = today + timedelta(days=30)

    gcal_entries = gcal.query(time_min, time_max)
    notion_entries = notion.query(time_min, time_max)

    # different scenarios
    ##############################################################################################################

    # events that have been newly created in notion and not added to gcal yet
    idx_new_notion_events = np.where(np.array(notion_entries['event_ids']) == None)[0]

    # events that have been newly created in gcal and not added to notion yet
    new_gcal_events = np.setdiff1d(gcal_entries['event_ids'], notion_entries['event_ids'], assume_unique=True)
    idx_new_gcal_events = [gcal_entries['event_ids'].index(item) for item in new_gcal_events]

    # events that have been modified in notion since last update
    idx_modified_notion_events = np.where(np.array(notion_entries['needs_update']))[0]

    # events that have been modified in gcal since last update
    common_ids = set(gcal_entries['event_ids']).intersection(notion_entries['event_ids'])
    idx_common_ids_notion = [notion_entries['event_ids'].index(item) for item in common_ids]
    idx_common_ids_gcal = [gcal_entries['event_ids'].index(item) for item in common_ids]

    # find common ids
    # for each common id, I need the index in gcal list and notion list
    # for each common id, check last updated property in gcal and notion
    idx_modified_gcal_events = []
    for notion_idx, gcal_idx in zip(idx_common_ids_notion, idx_common_ids_gcal):
        if gcal_entries['last_updated'][gcal_idx] > notion_entries['last_updated'][notion_idx]:
            idx_modified_gcal_events.append(gcal_idx)

    ###########################################################################################################


    # bring new events from gcal over to notion

    for idx in idx_new_gcal_events:
        name = gcal_entries['names'][idx]
        start_date = gcal_entries['start_dates'][idx]
        end_date = gcal_entries['end_dates'][idx]
        duration = gcal_entries['durations'][idx]
        gcal_id = gcal_entries['event_ids'][idx]
        calendar = gcal_entries['calendars'][idx]
        notion.add_entry(name=name, start_date=start_date, end_date=end_date, duration=duration, gcal_id=gcal_id, category=calendar)

    

