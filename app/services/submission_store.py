from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError


class SubmissionStoreUnavailable(Exception):
    pass


class SubmissionStore:
    def __init__(self, mongodb_url: str, database_name: str, collection_name: str):
        self.client = MongoClient(mongodb_url)
        self.collection = self.client[database_name][collection_name]

    def save_submission(self, site_id: str, ip_address: str | None, payload: dict[str, Any]) -> str:
        document = {
            "site_id": site_id,
            "ip_address": ip_address,
            "payload": payload,
        }

        try:
            result = self.collection.insert_one(document)
        except PyMongoError as exc:
            raise SubmissionStoreUnavailable("submission_store_unavailable") from exc

        return str(result.inserted_id)
