from Todoist import TodoIstAPI
from Notion import NotionAPI
from Gcal import GCalAPI
from config import notion_config, gcal_config, timezone, todoist_token, sync_gcal, sync_todoist
from datetime import datetime, timedelta, date
import numpy as np
import os
import pytz


# test


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
    idx_new_notion_events = list(np.where(np.array(notion_entries['gcal_ids']) is None)[0])
    idx_existing_start_dates = list(np.where(np.array(notion_entries['start_dates']) is not None)[0])
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
    idx_modified_notion_events = list(np.where(np.array(notion_entries['needs_update']))[0])
    idx_existing_start_dates = list(np.where(np.array(notion_entries['start_dates']) is not None)[0])
    idx_notion = list(set(idx_modified_notion_events).intersection(idx_existing_start_dates))

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
                start_date += timedelta(hours=gcal_config['Default Event Start'])
                print("Start time of '{}' set to {}".format(name, start_date))
            if not duration:
                duration = gcal_config['Default Event Length']
            end_date = start_date + timedelta(hours=duration)
        gcal.update_entry(calendar=calendar, gcal_id=gcal_id, name=name, start_date=start_date, end_date=end_date, description=None, source=None)
        notion.update_entry(page_id=page_id)
        print("Updated '{}' in GCal.".format(name))


def get_min_max_dates(max=30):
    today = date.today()
    time_min = today - timedelta(days=1)
    time_max = today + timedelta(days=max)
    return today, time_min, time_max


def run_sync(notion, todoist, gcal):
    today, time_min, time_max = get_min_max_dates(max=30)
    notion_entries = notion.query(time_min, time_max)

    if sync_todoist:
        print("start todoist sync")
        todoist_entries = todoist.get_tasks()
        for task in todoist_entries:
            if str(task['id']) in notion_entries['todoist_ids']:
                # update notion entry
                notion_idx = notion_entries['todoist_ids'].index(str(task['id']))  # find index of the matching id to get the notion page id
                page_id = notion_entries['notion_ids'][notion_idx]

                if task['due']:
                    prop = todoist.get_task_properties(task, name=True, task_id=True, done=True, labels=True, priority=True, date=True)
                    if notion_entries['start_dates'][notion_idx] != prop['start_date']:
                        notion.update_entry(page_id=page_id,
                                            name=prop['name'],
                                            start_date=prop['start_date'],
                                            end_date=prop['end_date'],
                                            duration=prop['duration'],
                                            todoist_id=prop['id'],
                                            done=prop['done'],
                                            labels=prop['labels'],
                                            priority=prop['priority'])
                    else:
                        prop = todoist.get_task_properties(task, name=True, task_id=True, done=True, labels=True, priority=True)
                        notion.update_entry(page_id=page_id, name=prop['name'], todoist_id=prop['id'], done=prop['done'], labels=prop['labels'], priority=prop['priority'])
                print("Updated '{}' in Notion.".format(task['content']))
            else:
                # make new notion entry
                if task['due']:
                    prop = todoist.get_task_properties(task, name=True, task_id=True, done=True, labels=True, priority=True, date=True)

                    if time_min + timedelta(days=1) <= prop['start_date'].date() < time_max:
                        notion.add_entry(name=prop['name'],
                                         start_date=prop['start_date'],
                                         end_date=prop['end_date'],
                                         duration=prop['duration'],
                                         todoist_id=prop['id'],
                                         category="Tasks",  # TODO: default calendar
                                         done=prop['done'],
                                         labels=prop['labels'],
                                         priority=prop['priority'])
                        print("Added '{}' to Notion.".format(task['content']))
                else:
                    prop = todoist.get_task_properties(task, name=True, task_id=True, done=True, labels=True, priority=True)
                    notion.add_entry(name=prop['name'], todoist_id=prop['id'], category="Tasks", done=prop['done'], labels=prop['labels'], priority=prop['priority'])
                    print("Added '{}' to Notion.".format(task['content']))

        # bring all new notion tasks to todoist
        idx_new_notion_events = np.where(np.array(notion_entries['todoist_ids']) == None)[0]  # and category == "tasks"
        idx_tasks = list(np.where(np.array(notion_entries['category']) is "Tasks")[0])  # TODO: default calendar
        idx_notion = list(set(idx_new_notion_events).intersection(idx_tasks))

        # update changed tasks in todoist
        idx_modified_notion_events = np.where(np.array(notion_entries['needs_update']))[0]  # and category == "tasks"
        idx_tasks = list(np.where(np.array(notion_entries['category']) is "Tasks")[0])  # TODO: default calendar
        idx_notion = list(set(idx_modified_notion_events).intersection(idx_tasks))
        print("end todoist sync")

    if sync_gcal:
        print('{} start syncing gcal'.format(datetime.now()))
        # idx_notion_entries_with_date = np.where(np.array(notion_entries['start_dates']) != None)[0]
        # notion_entries_with_date = [notion_entries[i] for i in idx_notion_entries_with_date]
        gcal_entries = gcal.query(time_min, time_max)
        # sync events
        bring_new_events_to_notion(notion, gcal_entries, notion_entries)
        update_events_in_notion(notion, gcal_entries, notion_entries)
        bring_new_events_to_gcal(notion, gcal, notion_entries)
        update_events_in_gcal(notion, gcal, notion_entries)

        print('{} finished syncing gcal'.format(datetime.now()))


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
