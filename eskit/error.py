import json


class ESKitError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


class CurlError(ESKitError):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


class ElasticsearchError(ESKitError):
    def __init__(self, status, response):

        self.status = status
        self.response = response
        error_type = None
        reason = None
        caused_by = None

        if isinstance(response, dict):
            error = response.get("error", {})
            if isinstance(error, dict):
                error_type = error.get("type")
                reason = error.get("reason")
                caused_by = error.get("caused_by")

        msg = f"HTTP {status}"
        if error_type:
            msg += f" [{error_type}]"
        if reason:
            msg += f": {reason}"
        if caused_by:
            msg += f": {caused_by}"

        super().__init__(msg)


class CacheError(ESKitError):
    pass


class ConfigNotFoundError(ESKitError):
    def __init__(self, path: str):
        super().__init__(f"Configuration file not found: {path}")
        self.path = path


class CurrentHostNotFoundError(ESKitError):
    def __init__(self, path: str):
        super().__init__(f"Current host file not found: {path}")
        self.path = path


class ConfigError(ESKitError):
    pass


class HostError(ESKitError):
    pass
