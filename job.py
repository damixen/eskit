#!/usr/bin/env python3
from dataclasses import dataclass, asdict

@dataclass
class ESKitJob:
    id: str
    name: str
    type: str  # reindex | rsync
    host: str
    status: str  # running | success | failed
    created_at: str
    updated_at: str
    payload: dict
    result: dict | None = None
    error: str | None = None

    log_path: str | None = None
    pid: int | None = None

    cache_path: str | None = None

    def get_output_id(self):
        return self.id
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            host=data["host"],
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            payload=data["payload"],
            result=data.get("result"),
            error=data.get("error"),
            cache_path=data.get("cache_path"),
            log_path=data.get("log_path"),
            pid=data.get("pid")
        )
    
    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "host": self.host,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "payload": self.payload,
            "log_path": self.log_path,
            "cache_path": self.cache_path,
            "pid": self.pid
        }

        if self.result is not None:
            data["result"] = self.result

        if self.error is not None:
            data["error"] = self.error

        return data