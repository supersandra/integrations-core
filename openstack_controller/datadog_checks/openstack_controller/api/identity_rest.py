# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)


class IdentityRest:
    def __init__(self, log, http, endpoint):
        self.log = log
        self.http = http
        self.endpoint = endpoint
        self.response_time_endpoint = self.endpoint
        self.domains_endpoint = '{}/v3/domains'.format(self.endpoint)
        self.projects_endpoint = '{}/v3/projects'.format(self.endpoint)
        self.users_endpoint = '{}/v3/users'.format(self.endpoint)
        self.groups_endpoint = '{}/v3/groups'.format(self.endpoint)
        self.group_users_endpoint = '{}/v3/groups/{{}}/users'.format(self.endpoint)
        self.services_endpoint = '{}/v3/services'.format(self.endpoint)

    def get_registered_limits(self):
        response = self.http.get('{}/registered_limits'.format(self.endpoint))
        response.raise_for_status()
        self.log.debug("response: %s", response.json())
        return response.json()['registered_limits']

    def get_limits(self):
        response = self.http.get('{}/limits'.format(self.endpoint))
        response.raise_for_status()
        self.log.debug("response: %s", response.json())
        return response.json()['limits']
