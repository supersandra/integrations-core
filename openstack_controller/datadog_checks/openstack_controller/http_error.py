# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from requests.exceptions import HTTPError


class ComponentNotFoundError(Exception):
    """Base class for all PyMongo exceptions."""


def http_error(message):
    def decorator_func(func):
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except HTTPError as e:
                self.log.error("%s: %s", message, e)

        return wrapper

    return decorator_func


def http_auth():
    def decorator_func(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except HTTPError as e:
                if e.response.status_code in (401, 403):
                    self.authorize()
                    try:
                        return func(self, *args, **kwargs)
                    except Exception as e:
                        self.log.error("%s", e)
                else:
                    self.log.error("%s", e)
            except Exception as e:
                self.log.error("%s", e)
                raise
            return None

        return wrapper

    return decorator_func
