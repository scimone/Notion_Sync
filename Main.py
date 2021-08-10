from Notion import NotionAPI
from Gcal import GCalAPI
from config import notion_config, gcal_config, timezone
from datetime import datetime, timedelta, date
import numpy as np


def bring_new_events_to_notion(notion, gcal_entries, notion_entries):
    # find events that have been newly created in gcal and not added to notion yet
    new_gcal_events = np.setdiff1d(gcal_entries['gcal_ids'], notion_entries['gcal_ids'], assume_unique=True)
    idx_new_gcal_events = [gcal_entries['gcal_ids'].index(item) for item in new_gcal_events]

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


def update_events_in_notion(notion, gcal_entries, notion_entries):
    # update events in notion that have been updated in gcal
    # events that have been modified in gcal since last update
    common_ids = set(gcal_entries['gcal_ids']).intersection(notion_entries['gcal_ids'])
    idx_common_ids_notion = [notion_entries['gcal_ids'].index(item) for item in common_ids]
    idx_common_ids_gcal = [gcal_entries['gcal_ids'].index(item) for item in common_ids]

    idx_modified_gcal_events = []
    for notion_idx, gcal_idx in zip(idx_common_ids_notion, idx_common_ids_gcal):
        if gcal_entries['last_updated'][gcal_idx] > notion_entries['last_updated'][notion_idx]:
            idx_modified_gcal_events.append([gcal_idx, notion_idx])

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


def bring_new_events_to_gcal(notion, gcal, notion_entries):
    # events that have been newly created in notion and not added to gcal yet
    idx_new_notion_events = np.where(np.array(notion_entries['gcal_ids']) == None)[0]

    # bring new events from notion to gcal
    calendar_names = gcal_config['Calendars'].keys()
    for idx in idx_new_notion_events:
        name = notion_entries['names'][idx]
        calendar = notion_entries['categories'][idx]
        start_date = notion_entries['start_dates'][idx]
        end_date = notion_entries['end_dates'][idx]
        duration = notion_entries['durations'][idx]
        if calendar not in calendar_names:
            calendar = gcal_config['Default Calendar']
        if not end_date:
            if (start_date.hour == 0) and (start_date.minute == 0):  # no time specified
                start_date += timedelta(hours=gcal_config['Default Event Start'])
                print("Start time of '{}' set to {}".format(name, start_date))
            if not duration:
                duration = gcal_config['Default Event Length']
            end_date = start_date + timedelta(hours=duration)
        page_id = notion_entries['notion_ids'][idx]
        gcal_id = gcal.add_entry(calendar=calendar, name=name, start_date=start_date, end_date=end_date, description=None, source=None)
        duration = (end_date - start_date).seconds / 3600
        notion.update_entry(page_id=page_id, gcal_id=gcal_id, category=calendar, duration=duration, start_date=start_date, end_date=end_date)
        print("Added '{}' to GCal.".format(name))


def update_events_in_gcal(notion, gcal, notion_entries):
    # events that have been modified in notion since last update
    idx_modified_notion_events = np.where(np.array(notion_entries['needs_update']))[0]

    # update events in gcal that have been updated in notion
    calendar_names = gcal_config['Calendars'].keys()
    for idx in idx_modified_notion_events:
        name = notion_entries['names'][idx]
        calendar = notion_entries['categories'][idx]
        start_date = notion_entries['start_dates'][idx]
        end_date = notion_entries['end_dates'][idx]
        duration = notion_entries['durations'][idx]
        gcal_id = notion_entries['gcal_ids'][idx]
        page_id = notion_entries['notion_ids'][idx]
        if calendar not in calendar_names:
            calendar = gcal_config['Default Calendar']
        if not end_date:
            if (start_date.hour == 0) and (start_date.minute == 0):  # no time specified
                start_date += timedelta(hours=gcal_config['Default Event Start'])
                print("Start time of '{}' set to {}".format(name, start_date))
            if not duration:
                duration = gcal_config['Default Event Length']
            end_date = start_date + timedelta(hours=duration)
        gcal.update_entry(calendar=calendar, gcal_id=gcal_id, name=name, start_date=start_date, end_date=end_date, description=None, source=None)
        notion.update_entry(page_id=page_id)
        print("Updated '{}' in GCal.".format(name))


def run_notion_gcal_sync():
    print('{} start syncing'.format(datetime.now()))
    # set up APIs
    gcal = GCalAPI(timezone, gcal_config)
    notion = NotionAPI(timezone, notion_config)

    # get all entries from today to next month
    today = date.today()
    time_min = today - timedelta(seconds=1)
    time_max = today + timedelta(days=30)
    gcal_entries = gcal.query(time_min, time_max)
    notion_entries = notion.query(time_min, time_max)

    # sync events
    bring_new_events_to_notion(notion, gcal_entries, notion_entries)
    update_events_in_notion(notion, gcal_entries, notion_entries)
    bring_new_events_to_gcal(notion, gcal, notion_entries)
    update_events_in_gcal(notion, gcal, notion_entries)

    print('{} finished syncing'.format(datetime.now()))


if __name__ == '__main__':
    run_notion_gcal_sync()