from Notion import NotionAPI
from Gcal import GCalAPI
from config import notion_config, gcal_config, timezone
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
    idx_new_notion_events = np.where(np.array(notion_entries['gcal_ids']) == None)[0]

    # events that have been newly created in gcal and not added to notion yet
    new_gcal_events = np.setdiff1d(gcal_entries['gcal_ids'], notion_entries['gcal_ids'], assume_unique=True)
    idx_new_gcal_events = [gcal_entries['gcal_ids'].index(item) for item in new_gcal_events]

    # events that have been modified in notion since last update
    idx_modified_notion_events = np.where(np.array(notion_entries['needs_update']))[0]

    # events that have been modified in gcal since last update
    common_ids = set(gcal_entries['gcal_ids']).intersection(notion_entries['gcal_ids'])
    idx_common_ids_notion = [notion_entries['gcal_ids'].index(item) for item in common_ids]
    idx_common_ids_gcal = [gcal_entries['gcal_ids'].index(item) for item in common_ids]

    idx_modified_gcal_events = []
    for notion_idx, gcal_idx in zip(idx_common_ids_notion, idx_common_ids_gcal):
        print(notion_entries['names'][notion_idx])
        print(gcal_entries['last_updated'][gcal_idx])
        print(notion_entries['last_updated'][notion_idx])
        if gcal_entries['last_updated'][gcal_idx] > notion_entries['last_updated'][notion_idx]:
            idx_modified_gcal_events.append([gcal_idx, notion_idx])

    ###########################################################################################################

    # bring new events from gcal to notion

    for idx in idx_new_gcal_events:
        name = gcal_entries['names'][idx]
        start_date = gcal_entries['start_dates'][idx]
        end_date = gcal_entries['end_dates'][idx]
        duration = gcal_entries['durations'][idx]
        gcal_id = gcal_entries['gcal_ids'][idx]
        calendar = gcal_entries['calendars'][idx]
        notion.add_entry(name=name, start_date=start_date, end_date=end_date, duration=duration, gcal_id=gcal_id, category=calendar)
        print("Added '{}' to Notion.".format(name))

    # update events in notion that have been updated in gcal
    for idx in idx_modified_gcal_events:
        gcal_idx, notion_idx = idx
        name = gcal_entries['names'][gcal_idx]
        start_date = gcal_entries['start_dates'][gcal_idx]
        end_date = gcal_entries['end_dates'][gcal_idx]
        duration = gcal_entries['durations'][gcal_idx]
        gcal_id = gcal_entries['gcal_ids'][gcal_idx]
        calendar = gcal_entries['calendars'][gcal_idx]
        page_id = notion_entries['notion_ids'][notion_idx]
        notion.update_entry(page_id=page_id, name=name, start_date=start_date, end_date=end_date, duration=duration, gcal_id=gcal_id, category=calendar)
        print("Updated '{}' in Notion.".format(name))

    # bring new events from notion to gcal
    calendar_names = gcal_config['Calendars'].keys()
    for idx in idx_new_notion_events:
        name = notion_entries['names'][idx]
        calendar = notion_entries['categories'][idx]
        start_date = notion_entries['start_dates'][idx]
        end_date = notion_entries['end_dates'][idx]
        duration = notion_entries['durations'][idx]
        if not calendar in calendar_names:
            calendar = gcal_config['Default Calendar']
        if not end_date:
            if (start_date.hour == 0) and (start_date.minute == 0):  # no time specified
                start_date += timedelta(hours=gcal_config['Default Event Start'])
                print("Start time of '{}' set to {}".format(name, start_date))
            if not duration:
                duration = gcal_config['Default Event Length']
            end_date = start_date + timedelta(hours=duration)
        page_id = notion_entries['notion_ids'][idx]
        gcal_id = gcal.add_entry(calendar=calendar, name=name, timezone=timezone, start_date=start_date, end_date=end_date, description=None, source=None)
        duration = (end_date - start_date).seconds / 3600
        notion.update_entry(page_id=page_id, gcal_id=gcal_id, category=calendar, duration=duration, start_date=start_date, end_date=end_date)
        print("Added '{}' to GCal.".format(name))
