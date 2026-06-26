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

        if isinstance(response, dict):
            error = response.get("error", {})

            if isinstance(error, dict):
                error_type = error.get("type")
                reason = error.get("reason")

        msg = f"HTTP {status}"
        if error_type:
            msg += f" [{error_type}]"
        if reason:
            msg += f": {reason}"

        super().__init__(msg)


class CacheError(ESKitError):
    pass


class ConfigError(ESKitError):
    pass


class HostError(ESKitError):
    pass
