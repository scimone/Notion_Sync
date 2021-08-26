from Todoist import TodoIstAPI
from Notion import NotionAPI
from Gcal import GCalAPI
from config import notion_config, gcal_config, timezone, todoist_token, sync_gcal, sync_todoist, DEFAULT_EVENT_START, DEFAULT_EVENT_LENGTH
from datetime import datetime, timedelta, date
import numpy as np
import os
import pytz


def bring_new_gcal_events_to_notion(notion, gcal_entries, notion_entries):
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


def update_gcal_events_in_notion(notion, gcal_entries, notion_entries):
    # update events in notion that have been updated in gcal
    # events that have been modified in gcal since last update
    common_ids = set(gcal_entries['gcal_ids']).intersection(notion_entries['gcal_ids'])
    idx_common_ids_notion = [notion_entries['gcal_ids'].index(item) for item in common_ids]
    idx_common_ids_gcal = [gcal_entries['gcal_ids'].index(item) for item in common_ids]

    idx_modified_gcal_events = []
    idx_notion_events_to_modify = []
    for notion_idx, gcal_idx in zip(idx_common_ids_notion, idx_common_ids_gcal):
        if gcal_entries['last_updated'][gcal_idx] > notion_entries['last_updated'][notion_idx]:
            idx_modified_gcal_events.append(gcal_idx)
            idx_notion_events_to_modify.append(notion_idx)

    for gcal_idx, notion_idx in zip(idx_modified_gcal_events, idx_notion_events_to_modify):
        notion.update_entry(
            name=gcal_entries['names'][gcal_idx],
            start_date=gcal_entries['start_dates'][gcal_idx],
            end_date=gcal_entries['end_dates'][gcal_idx],
            duration=gcal_entries['durations'][gcal_idx],
            gcal_id=gcal_entries['gcal_ids'][gcal_idx],
            category=gcal_entries['calendars'][gcal_idx],
            page_id=notion_entries['notion_ids'][notion_idx]
        )
        notion_entries = notion.update_local_data(notion_entries, notion_idx, gcal_entries['start_dates'][gcal_idx], gcal_entries['end_dates'][gcal_idx], gcal_entries['durations'][gcal_idx])
        print("Updated '{}' in Notion.".format(gcal_entries['names'][gcal_idx]))
    return notion_entries, idx_notion_events_to_modify


def bring_new_events_to_gcal(notion, gcal, notion_entries):
    # events that contain dates and have been newly created in notion and not added to gcal yet
    idx_new_notion_events = list(np.where(np.array(notion_entries['gcal_ids']) == None)[0])
    idx_existing_start_dates = list(np.where(np.array(notion_entries['start_dates']) != None)[0])
    idx_notion = list(set(idx_new_notion_events).intersection(idx_existing_start_dates))

    # bring new events from notion to gcal
    calendar_names = gcal_config['Calendars'].keys()
    for idx in idx_notion:
        name = notion_entries['names'][idx]
        calendar = notion_entries['categories'][idx]
        start_date = notion_entries['start_dates'][idx]
        end_date = notion_entries['end_dates'][idx]
        duration = notion_entries['durations'][idx]
        if calendar not in calendar_names:
            calendar = gcal_config['Default Calendar']
        if not end_date:
            if (start_date.hour == 0) and (start_date.minute == 0):  # no time specified
                start_date += timedelta(hours=DEFAULT_EVENT_START)
                print("Start time of '{}' set to {}".format(name, start_date))
            if not duration:
                duration = DEFAULT_EVENT_LENGTH
            end_date = start_date + timedelta(hours=duration)
        page_id = notion_entries['notion_ids'][idx]
        gcal_id = gcal.add_entry(calendar=calendar, name=name, start_date=start_date, end_date=end_date, description=None, source=None)
        duration = (end_date - start_date).seconds / 3600
        notion.update_entry(page_id=page_id, gcal_id=gcal_id, category=calendar, duration=duration, start_date=start_date, end_date=end_date)
        print("Added '{}' to GCal.".format(name))


def update_events_in_gcal(notion, gcal, notion_entries, by_todoist_modified_notion_events):
    # events that have been modified in notion since last update
    idx_modified_notion_events = list(np.where(np.array(notion_entries['needs_update']))[0])
    idx_existing_start_dates = list(np.where(np.array(notion_entries['start_dates']) is not None)[0])
    idx_existing_gcal_ids = list(np.where(np.array(notion_entries['gcal_ids']) is not None)[0])

    idx_notion = list(set.intersection(*map(set, [idx_modified_notion_events, idx_existing_start_dates, idx_existing_gcal_ids]))) + by_todoist_modified_notion_events

    # update events in gcal that have been updated in notion
    calendar_names = gcal_config['Calendars'].keys()
    for idx in idx_notion:
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
                start_date += timedelta(hours=DEFAULT_EVENT_START)
                print("Start time of '{}' set to {}".format(name, start_date))
            if not duration:
                duration = DEFAULT_EVENT_LENGTH
            end_date = start_date + timedelta(hours=duration)
        gcal.update_entry(calendar=calendar, gcal_id=gcal_id, name=name, start_date=start_date, end_date=end_date, description=None, source=None)
        notion.update_entry(page_id=page_id)
        print("Updated '{}' in GCal.".format(name))


def update_todoist_entries_in_notion(notion, todoist, task, notion_entries):
    notion_idx = notion_entries['todoist_ids'].index(str(task['id']))  # find index of the matching id to get the notion page id
    page_id = notion_entries['notion_ids'][notion_idx]

    prop = todoist.get_task_properties(task, duration=notion_entries['durations'][notion_idx])
    notion.update_entry(page_id=page_id,
                        name=prop['name'],
                        start_date=prop['start_date'],
                        end_date=prop['end_date'],
                        todoist_id=prop['id'],
                        done=prop['done'],
                        labels=prop['labels'],
                        priority=prop['priority'])

    notion_entries = notion.update_local_data(notion_entries, notion_idx, prop['start_date'], prop['end_date'], notion_entries['durations'][notion_idx])

    print("Updated '{}' in Notion.".format(task['content']))
    return notion_idx, notion_entries


def bring_new_todoist_entries_to_notion(todoist, notion, task, time_min, time_max):
    prop = todoist.get_task_properties(task)

    if time_min + timedelta(days=1) <= prop['start_date'].date() < time_max:
        notion.add_entry(name=prop['name'],
                         start_date=prop['start_date'],
                         end_date=prop['end_date'],
                         duration=prop['duration'],
                         todoist_id=prop['id'],
                         category=gcal_config["Default Calendar"],
                         done=prop['done'],
                         labels=prop['labels'],
                         priority=prop['priority'])
        print("Added '{}' to Notion.".format(task['content']))


def bring_new_notion_entries_to_todoist(todoist, notion_entries):
    # bring all new notion tasks to todoist
    idx_new_notion_events = np.where(np.array(notion_entries['todoist_ids']) == None)[0]
    idx_tasks = list(np.where(np.array(notion_entries['categories']) == gcal_config["Default Calendar"])[0])
    idx_notion = list(set(idx_new_notion_events).intersection(idx_tasks))

    for idx in idx_notion:
        start_date = notion_entries['start_dates'][idx]
        if (start_date.hour == 0) and (start_date.minute == 0):  # no time specified
            start_date += timedelta(hours=DEFAULT_EVENT_START)
        todoist.add_entry(
            name=notion_entries['names'][idx],
            start_date=start_date,
            priority=todoist.get_priority(notion_entries['priorities'][idx], todoist_format=True),
            parent_id=None,
            labels=todoist.get_labels([label['name'] for label in notion_entries['labels'][idx]], todoist_format=True)
        )
        print("Added '{}' to Todoist.".format(notion_entries['names'][idx]))
    return idx_notion


def get_indices_for_todoist_update(notion_entries):
    idx_modified_notion_events = np.where(np.array(notion_entries['needs_update']))[0]
    idx_tasks = list(np.where(np.array(notion_entries['categories']) == gcal_config['Default Calendar'])[0])
    idx_notion = list(set(idx_modified_notion_events).intersection(idx_tasks))
    return idx_notion


def update_notion_entries_in_todoist(notion, todoist, notion_entries, idx_notion=None):
    # update changed tasks in todoist
    if not idx_notion:
        idx_notion = get_indices_for_todoist_update(notion_entries)

    for idx in idx_notion:
        page_id = notion_entries['notion_ids'][idx]
        todoist_id = notion_entries['todoist_ids'][idx]
        todoist.update_entry(
            int(todoist_id),
            name=notion_entries['names'][idx],
            start_date=notion_entries['start_dates'][idx],
            priority=todoist.get_priority(notion_entries['priorities'][idx], todoist_format=True),
            parent_id=None,
            labels=todoist.get_labels([label['name'] for label in notion_entries['labels'][idx]], todoist_format=True)
        )
        todoist.check_or_uncheck_item(int(todoist_id), notion_entries['done'][idx])
        notion.update_entry(page_id=page_id)
        print("Updated '{}' in Todoist.".format(notion_entries['names'][idx]))


def commit_todoist_and_update_notion(notion, todoist, notion_entries, idx_notion):

    commit = todoist.api.commit()
    if commit and idx_notion:
        for idx, item in zip(idx_notion, commit['items']):
            page_id = notion_entries['notion_ids'][idx]
            todoist_id = item['id']
            todoist.check_or_uncheck_item(todoist_id, notion_entries['done'][idx])
            notion.update_entry(page_id=page_id, todoist_id=str(todoist_id))
        todoist.api.commit()


def get_min_max_dates(max=30):
    today = date.today()
    time_min = today - timedelta(days=1)
    time_max = today + timedelta(days=max)
    return today, time_min, time_max


def run_sync(notion, todoist, gcal):
    today, time_min, time_max = get_min_max_dates(max=30)
    notion_entries = notion.query(time_min, time_max)

    if sync_todoist:
        print('{} todoist sync started'.format(datetime.now()))
        todoist_entries = todoist.get_tasks()
        by_todoist_modified_notion_events = []
        for task in todoist_entries:
            if not type(task['id']) == str:
                if str(task['id']) in notion_entries['todoist_ids']:
                    notion_idx, notion_entries = update_todoist_entries_in_notion(notion, todoist, task, notion_entries)
                    if task['due']:
                        by_todoist_modified_notion_events.append(notion_idx)
                else:
                    if not bool(task['is_deleted']):
                        bring_new_todoist_entries_to_notion(todoist, notion, task, time_min, time_max)

        idx_notion = bring_new_notion_entries_to_todoist(todoist, notion_entries)
        update_notion_entries_in_todoist(notion, todoist, notion_entries)

        print('{} todoist sync finished'.format(datetime.now()))
    else:
        by_todoist_modified_notion_events = []

    if sync_gcal:
        print('{} gcal sync started'.format(datetime.now()))
        gcal_entries = gcal.query(time_min, time_max)
        # sync events
        bring_new_gcal_events_to_notion(notion, gcal_entries, notion_entries)
        notion_entries, by_gcal_modified_notion_events = update_gcal_events_in_notion(notion, gcal_entries, notion_entries)
        bring_new_events_to_gcal(notion, gcal, notion_entries)
        update_events_in_gcal(notion, gcal, notion_entries, by_todoist_modified_notion_events)

        print('{} gcal sync finished'.format(datetime.now()))
    else:
        by_gcal_modified_notion_events = []

    if todoist:  # update by gcal modified tasks in todoist
        update_notion_entries_in_todoist(notion, todoist, notion_entries, by_gcal_modified_notion_events)
        commit_todoist_and_update_notion(notion, todoist, notion_entries, idx_notion)


def create_notion_api():
    notion = NotionAPI(timezone, notion_config)
    return notion


def create_todoist_api():
    todoist = TodoIstAPI(todoist_token)
    return todoist


def create_gcal_api():
    gcal = GCalAPI(timezone, gcal_config)
    return gcal


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

    run_sync(notion, todoist, gcal)
