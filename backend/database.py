import os
from typing import Any, Dict, Optional, List
from datetime import datetime
from pymongo import MongoClient

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "studioaljo")

_client: Optional[MongoClient] = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(DATABASE_URL)
    return _client


def get_db():
    return get_client()[DATABASE_NAME]

# Export a database handle for convenience
db = get_db()


def create_document(collection_name: str, data: Dict[str, Any]) -> str:
    now = datetime.utcnow()
    payload = {**data, "created_at": now, "updated_at": now}
    result = db[collection_name].insert_one(payload)
    return str(result.inserted_id)


def get_documents(collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 50) -> List[Dict[str, Any]]:
    filter_dict = filter_dict or {}
    cursor = db[collection_name].find(filter_dict).sort("created_at", -1).limit(limit)
    docs: List[Dict[str, Any]] = []
    for d in cursor:
        d["_id"] = str(d["_id"])  # stringify ObjectId
        docs.append(d)
    return docs
