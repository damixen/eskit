#!/usr/bin/env python3
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class ESKitArchive:
    name: str
    type: str
    remote_src: str
    local_dst: str
    repos: Dict
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            type=data["type"],
            remote_src=data["remote_src"],
            local_dst=data["local_dst"],
            repos=data["repos"]
        )
    
    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "type": self.type,
            "src": self.remote_src,
            "dst": self.local_dst,
            "repos":self.repos
        }

        return data
    
@dataclass
class ESKitArchiveState:
    name: str
    created_at: str
    updated_at: str
    created_at_ms:int
    updated_at_ms:int

    last_pull: str

    remote_src_stat: Dict
    local_dst_stat: Dict

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            created_at_ms=data["created_at_ms"],
            updated_at_ms=data["updated_at_ms"],
            last_pull=data["last_pull"],
            remote_src_stat=data["remote_src_stat"],
            local_dst_stat=data["local_dst_stat"]
        )
    
    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "created_at": self.created_at,
            "created_at_ms": self.created_at_ms,
            "updated_at_ms": self.updated_at_ms,
            "updated_at": self.updated_at,
            "last_pull": self.last_pull,
            "src_stats": self.remote_src_stat,
            "dst_stats":self.local_dst_stat
        }

        return data