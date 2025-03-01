from collections import namedtuple
import sys
import os



def namedtuple_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    cls = namedtuple("Row", fields)
    return cls._make(row)

date_format = '%Y-%m-%d %H:%M'



def Resource_Path(
    relative_path,
):  
    """ Call to make the software executable and stand alone"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
