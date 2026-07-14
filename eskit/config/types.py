from typing import TypedDict


class HostConfig(TypedDict):
    name: str
    ip: str
    ssh: dict
    elastic: dict
    push_protected: bool


class ReindexConfig(TypedDict):
    name: str
    mappings: dict


class Config(TypedDict):
    hosts: list[HostConfig]
    views: dict
    reindex_configs: list[ReindexConfig]


class FileStat(TypedDict):
    name: str
    mode: str
    owner: str
    group: str
    mtime_ms: int
    atime_ms: int
    ctime_ms: int
    mtime_iso: str
    atime_iso: str
    ctime_iso: str
    size: int
