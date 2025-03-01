import sys
from controller import Controller
import utils
import datetime as dt
import argparse
from tabulate import tabulate
import os
import json


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="work history recorder")

    # Add the command argument
    parser.add_argument("command", help="The command to execute")
    
    # Add the details argument(s)
    parser.add_argument("details", nargs="*", help="Additional details for the command")

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    command_str = args.command
    detail_str = args.details

    db = Controller(utils.Resource_Path('year1403.db'))

    config_path = utils.Resource_Path('config.json')
    if not os.path.exists(config_path) :
        month = input('Enter Current Month: ')
        with open(config_path, 'w') as json_file:
            json.dump({'month': month}, json_file)
    else:
        if command_str == 'month':
            if len(detail_str) == 1:
                os.remove(config_path)
                month = detail_str[0]
                with open(config_path, 'w') as json_file:
                    json.dump({'month': month}, json_file)
            else: 
                raise NameError('month name should be one word only')
        else:
            with open(config_path) as json_file:
                month = json.load(json_file).get('month', None)
                if month is None:
                    raise LookupError('Config.json file has no month key.')
    


    db.start_new_month(month)

    if command_str == 'start':
        if len(detail_str) == 3:
            category, activity, start_str = detail_str
        elif len(detail_str) == 1:
            start_str = detail_str[0]
            category = input("Category: ")
            activity = input("Activity: ")
        else:
            start_str = input("Start Time: ")
            category = input("Category: ")
            activity = input("Activity: ")
        if start_str in ['now', '']:
            start_time = dt.datetime.now()
        else:
            start_time = dt.datetime.strptime(start_str, utils.date_format)
        db.start_new_session(month_name=month, start_time=start_time, category=category, activity=activity)
        result = db.view_last_session(month_name=month)
        column_names = [description[0] for description in db.cur.description]
        table = tabulate(result, headers=column_names, tablefmt="grid")
        print(table)
    elif command_str in ['stop', 'end']:
        stop_str = detail_str[0]
        if stop_str == 'now':
            stop_time = dt.datetime.now()
        else:
            stop_time = dt.datetime.strptime(stop_str, utils.date_format)
        db.stop_last_session(month_name=month, stop_time=stop_time)
        result = db.view_last_session(month_name=month)
        column_names = [description[0] for description in db.cur.description]
        table = tabulate(result, headers=column_names, tablefmt="grid")
        print(table)
    elif command_str in ['show', 'view']:
        filter_exclude = False
        if len(detail_str) == 0: 
            filter_string = None
        else:
            if detail_str[0] == 'not':
                filter_exclude = True  
                filter_string = " ".join(detail_str[1:]) 
            else:
                filter_string = " ".join(detail_str) 

        result, sum_value = db.view_all_sessions(
            month_name=month, 
            category_filter=filter_string, 
            exclude=filter_exclude 
        )
        column_names = [description[0] for description in db.cur.description]
        table = tabulate(result, headers=column_names, tablefmt="grid")
        print(table)
        print(f"{'*'*20}\nSUM OF DURATIONS IS {sum_value:.2f}\n{'*'*20}")
    elif command_str in ['delete', 'remove']:
        if detail_str[0] == 'last':
            result = db.delete_last_record(month_name=month)
            result = db.view_last_session(month_name=month, n_last_rows=3)
            column_names = [description[0] for description in db.cur.description]
            table = tabulate(result, headers=column_names, tablefmt="grid")
            print(table)
    elif command_str in ['export']:
        filter_exclude = False
        if len(detail_str) == 0: 
            filter_string = None
        else:
            if detail_str[0] == 'not':
                filter_exclude = True  
                filter_string = " ".join(detail_str[1:]) 
            else:
                filter_string = " ".join(detail_str) 
        db.export_to_csv(month_name=month, category_filter=filter_string, exclude=filter_exclude)

    db.disconnect()

