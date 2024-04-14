from typing import Any
from carthooks import Client
from .logger import Logger
import os
import time

class Task:
    def __init__(self, handler, app_id, collection_id, 
                trigger="pulling_items", 
                filter=None, 
                pagelimit=1,
                include_locked=False,
                sort=['created'], 
                pulling_interval=30):
        self.handler = handler
        self.trigger = trigger
        self.last_pull = 0
        self.pulling_options = {
            "app_id": app_id,
            "collection_id": collection_id,
            "filter": filter,
            "sort": sort,
            "pulling_interval": pulling_interval,
            "pagelimit": pagelimit,
            "include_locked": include_locked
        }
    
    def pulling_now(self):
        self.last_pull = time.time()

    def is_pull_able(self):
        return time.time() - self.last_pull > self.pulling_options["pulling_interval"]

class Record:
    def __init__(self, sailor, app_id, collection_id, item_id, data):
        self.sailor = sailor
        self.app_id = app_id
        self.collection_id = collection_id
        self.item_id = item_id
        self.__record = data
        self.id = data["id"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.title = data["title"]
        self.data = data["fields"]
    
    def __getitem__(self, key):
        return self.__record.get(key)

    def __str__(self) -> str:
        return f"Record(title={self.__record.get('title')}, item_id={self.item_id})"
    
    def __repr__(self) -> str:
        return f"Record(app_id={self.app_id}, collection_id={self.collection_id}, item_id={self.item_id})"
    
    def lock(self, **kwargs):
        return self.sailor.lock(self, **kwargs)
    
    def unlock(self):
        return self.sailor.unlock(self)
    
    def update(self, map):
        return self.sailor.update(self, map)

    
class Context:
    def __init__(self, sailor, task, logger):
        self.task = task
        self.sailor = sailor
        self.logger = logger

    # def __getattribute__(self, __name: str) -> Any:
    #     return self.sailor.client.__getattribute__(__name)

    # def create(self, app_id, collection_id, data):
    #     return self.sailor.create(app_id, collection_id, data)

class Sailor:
    def __init__(self, token=None, sailor_id=None):
        self.tasks = []
        self.logger = Logger("cybersailor")
        self.client = Client()
        self.client.setAccessToken(token)
        if sailor_id == None:
            self.sailor_id = os.uname().nodename
        else:
            self.sailor_id = sailor_id

    def subscribe(self, **kwargs):
        task = Task(**kwargs)
        self.tasks.append(task)

    def lock(self, record, lock_timeout=600, subject=None):
        self.logger.debug(f"Locking task: {record}")
        return self.client.lockItem(record.app_id, record.collection_id, record.item_id, lock_timeout=lock_timeout, lock_id=self.sailor_id, subject=subject)

    def unlock(self, record):
        self.logger.debug(f"Unlocking task: {record}")
        return self.client.unlockItem(record.app_id, record.collection_id, record.item_id, lock_id=self.sailor_id)

    def update(self, task, map):
        self.logger.debug(f"Updating task: {task} with map: {map}")
        return self.client.updateItem(task.app_id, task.collection_id, task.item_id, map)

    def create(self, app_id, collection_id, data):
        self.logger.debug(f"Creating record in app_id: {app_id}, collection_id: {collection_id} with data: {data}")
        result = self.client.createItem(app_id, collection_id, data)
        return result

    def run(self):
        self.logger.debug("Running...")

        while True:
            for task in self.tasks:
                if task.trigger == "pulling_items" and task.is_pull_able():
                    self.pull(task)
            time.sleep(1)

    def pull(self,task):
        try:
            app_id = task.pulling_options["app_id"]
            collection_id = task.pulling_options["collection_id"]
            self.logger.debug(f"Pulling items from app_id: {app_id}, collection_id: {collection_id}")

            options = {
                "limit": task.pulling_options["pagelimit"],
            }

            if task.pulling_options["sort"] != None:
                options["sort"] = task.pulling_options["sort"]

            if task.pulling_options["filter"] != None:
                for column in task.pulling_options["filter"]:
                    for operator in task.pulling_options["filter"][column]:
                        options[f"filters[{column}][{operator}]"] = task.pulling_options["filter"][column][operator]

            if task.pulling_options["include_locked"] == False:
                options["unlockedOrLockedBy"] = self.sailor_id

            # print(options)

            result = self.client.getItems(app_id, collection_id, **options)
            
            items = result.data
            task.pulling_now()
            if items.__len__() > 0:
                context = Context(sailor=self, task=task, logger=self.logger)
                for item in items:
                    self.logger.debug(f"Handling item: {item['id']}")
                    record = Record(sailor=self, app_id=app_id, collection_id=collection_id, item_id=item['id'], data=item)
                    self.logger.debug(f"Record: {record}")
                    try:
                        task.handler(context, record)
                    except Exception as e:
                        self.logger.error(f"Error: {e}")
        except Exception as e:
            self.logger.error(f"Error: {e}")
            time.sleep(5)