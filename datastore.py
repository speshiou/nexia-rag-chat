from datetime import datetime
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import certifi
import config

class Datastore:
    def __init__(self):
        self.client: MongoClient = MongoClient(config.MONGODB_URI, tlsCAFile=certifi.where())
        self.db: Database = self.client["nexia-rag"]
        # collections
        self.tickets: Collection = self.db["tickets"]

    def upsert_chat(self, chat_id: int) -> None:
        default_data = {
            "first_interaction": datetime.utcnow(),
            "history": [],
        }

        data = {
            "last_interaction": datetime.utcnow(),
        }

        filter = {
            "_id": chat_id
        }

        update = {
            "$set": data,
            "$setOnInsert": default_data,
        }

        self.tickets.update_one(filter, update, upsert=True)

    def get_chat_history(self, chat_id: int):
        filter = {
            "_id": chat_id
        }

        doc = self.tickets.find_one(filter)
        return doc["history"] if doc else []
    
    def push_chat_history(self, chat_id: int, user_message: str, model_message: str, num_max_history: int = -1):
        filter = {
            "_id": chat_id
        }

        new_messages = {
            "user": user_message,
            "model": model_message,
        }

        if num_max_history > 0:
            self.tickets.update_one(
                filter,
                {
                    "$push": {
                        "history": {
                            "$each": [ new_messages ],
                            "$slice": -num_max_history,
                        }
                    }
                }
            )
        else:
            self.tickets.update_one(
                filter,
                {
                    "$push": {
                        "history": new_messages
                    }
                }
            )

    def clear_chat_history(self, chat_id: int):
        filter = {
            "_id": chat_id
        }

        update = {
            "$set": {
                "history": []
            }
        }

        self.tickets.update_one(filter, update)