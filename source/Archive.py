import shelve, time, sys, os
from pathlib import Path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Archive:
    def __init__(self, name:str, interval=60.0):
        """
        shelve structure: each object has its own archive, each archive is a db, each db is a file, each file is a shelve
        
        In the db: each key is the timestamp, each value is the object at the time of the timestamp

        """
        self.name = name
        self.last_archive_time = time.time() # NOTE: does not necessarily reflect the date of items in the archive, just the time that the archive was last updated, do this in clock time, not sim time
        self.interval = interval
        self.archive_path = Path(parent_dir) / Path("archive")/ Path(self.name)

    def put(self, key, value):
        with shelve.open(fr'{self.archive_path}', writeback=True) as db:
            db[str(key)] = value

    def get(self, key):
        with shelve.open(self.archive_path) as db:
            return db[str(key)]

    def store(self, data):
        if self.last_archive_time+self.interval <= time.time():
            with shelve.open(fr'{self.archive_path}', writeback=True) as db:
                archive_time = time.time()
                db[str(archive_time)] = data
            self.last_archive_time = archive_time

    def retrieve(self):
        with shelve.open(self.archive_path) as db:
            return db[str(self.last_archive_time)]
        
    def retrieve_all(self):
        with shelve.open(self.archive_path) as db:
            return list(db.items())
            
            