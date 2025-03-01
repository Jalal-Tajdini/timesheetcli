import sqlite3 as s3
import os
import typing as ty
import datetime as dt
import utils
import csv

class Controller:
    def __init__(self, db_name: str):
        self.db = db_name
        try:
            self.conn = s3.connect(db_name)
            self.conn.row_factory = utils.namedtuple_factory
            self.cur = self.conn.cursor()
        except Exception as e:
            raise ConnectionError(f'Can not connect to "{db_name}":\n{e}')

    def disconnect(self):
        try:
            self.conn.close()
        except Exception as e:
            raise ConnectionError(f'Can not disconnect from "{self.db}"\n{e}')

    def execute(self, sql_cmd: str, parameters: ty.Union[list, tuple]):
        self.cur.execute(sql_cmd, parameters)
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ConnectionError(
                f'Can not commit command {sql_cmd} with parameters "{parameters}":\n{e}'
            )

    def start_new_month(self, month_name: str):
        sql_command = f"CREATE TABLE IF NOT EXISTS {month_name} (id INTEGER PRIMARY KEY AUTOINCREMENT,category VARCHAR(255),activity VARCHAR(255),start DATETIME,end DATETIME,duration FLOAT)"
        self.cur.execute(sql_command)
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ConnectionError(f"Can not create table {month_name}:\n{e}")

    def start_new_session(
        self, month_name: str, category: str, activity: str, start_time: dt.datetime
    ):
        start_time = dt.datetime.strftime(start_time, utils.date_format)
        sql_command = f"INSERT INTO {month_name} (category, activity, start) VALUES ('{category}' ,'{activity}','{start_time}');"
        self.cur.execute(sql_command)

        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ConnectionError(f"Can not insert new session for {month_name}:\n{e}")
    
    
    def stop_last_session(
            self, month_name:str, stop_time: dt.datetime
    ):

        last_row = self.get_last_row(month_name)
        if last_row is None: 
            raise LookupError(f"Can not stop last session. No rows found in table '{month_name}'!")
        else:
            last_row = last_row
        start_time = dt.datetime.strptime(last_row.start, utils.date_format)
        duration = (stop_time - start_time).seconds / 3600
        stop_time = dt.datetime.strftime(stop_time, utils.date_format)

        sql_command = f"UPDATE {month_name} SET end=\'{stop_time}\', duration={duration} WHERE id={last_row.id};"
        self.cur.execute(sql_command)
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ConnectionError(f"Can not insert new session for {month_name}:\n{e}")

    def get_last_row(self, month_name:str):
        self.cur.execute(f"SELECT id, start FROM {month_name} ORDER BY id DESC LIMIT 1;")
        return self.cur.fetchone()


    def view_last_session(self, month_name:str, n_last_rows:int=1):
        sql_command = f"SELECT * from {month_name} ORDER BY id DESC LIMIT {n_last_rows};"
        results = self.cur.execute(sql_command)
        return results.fetchall()

    def view_all_sessions(self, month_name:str, category_filter:str=None, exclude:bool=False):
        if category_filter:
            if exclude:
                sql_command = f"SELECT * from {month_name} WHERE category != '{category_filter}';"
            else:
                sql_command = f"SELECT * from {month_name} WHERE category = '{category_filter}';"
        else:
            sql_command = f"SELECT * from {month_name};"
        results = self.cur.execute(sql_command)
        detailed_report = results.fetchall()
        sum_result = self.cur.execute(sql_command.replace('*', 'sum(duration) AS duration_sum'))
        sum_report = sum_result.fetchone().duration_sum
        return detailed_report, sum_report if sum_report else 0

    def delete_last_record(self, month_name:str):
        sql_command = f"DELETE FROM {month_name} WHERE id=(SELECT MAX(id) FROM {month_name})"
        self.cur.execute(sql_command)
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ConnectionError(f"Can not delete last record for {month_name}:\n{e}")

    def export_to_csv(self, month_name:str, category_filter:str=None, exclude:bool=False):
        
        try:
            # Get all data from the specified table
            if category_filter:
                if exclude:
                    query_str = f"SELECT * FROM {month_name} WHERE category != '{category_filter}'"
                else:
                    query_str = f"SELECT * FROM {month_name} WHERE category = '{category_filter}'"
            else:
                query_str = f"SELECT * FROM {month_name}"
            
            self.cur.execute(query_str)
            rows = self.cur.fetchall()

            if not rows:
                print(f"No data found in table '{month_name}'")
                return

            # Get column names
            column_names = [description[0] for description in self.cur.description]
            if category_filter:
                if exclude:
                    category_filter += " excluded"
                file_name = f"Timesheet for {month_name}-{category_filter}.csv"
            else:
                file_name = f"Timesheet for {month_name}.csv"
            file_path = os.path.join(os.path.expanduser("~"), "Desktop", file_name)

            # Write data to CSV file
            with open(file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                
                # Write header
                csv_writer.writerow(column_names)
                
                # Write data rows
                for row in rows:
                    csv_writer.writerow(row)

            print(f"Data exported successfully to {file_path}")

        except Exception as e:
            raise Exception(f"Error exporting data to CSV: {e}")


if __name__ == "__main__":
    db = Controller("year.db")
    db.start_new_month("tir")
    db.start_new_session("tir", "software", "add diagnosis", dt.datetime.now())
    db.view_last_session("tir", 1)
    db.stop_last_session("tir", dt.datetime.now())
    db.view_last_session("tir", 1)
    db.disconnect()
