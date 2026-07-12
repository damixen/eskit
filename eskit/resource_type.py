from enum import Enum


class ResourceType(str, Enum):
    HOST = "host"
    INDEX = "index"
    SNAPSHOT = "snapshot"
    REPOSITORY = "repository"
    ARCHIVE = "archive"
    CONFIG = "config"
    CACHE = "cache"
    TASK = "task"
    JOB = "job"

    def __str__(self):
        return self.value
