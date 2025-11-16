from datetime import datetime
import json
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for audit data"""

    def default(self, obj):
        if isinstance(obj, (UUID, datetime)):
            return str(obj)
        return super().default(obj)


def to_json(data: dict) -> dict:
    """Prepare dictionary for JSON serialization"""
    if not data:
        return data
    return json.loads(json.dumps(data, cls=JSONEncoder))
