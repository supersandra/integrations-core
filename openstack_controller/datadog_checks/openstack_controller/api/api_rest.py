# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import re

from datadog_checks.openstack_controller.api.api import Api
from datadog_checks.openstack_controller.api.baremetal_rest import BaremetalRest
from datadog_checks.openstack_controller.api.block_storage_rest import BlockStorageRest
from datadog_checks.openstack_controller.api.compute_rest import ComputeRest
from datadog_checks.openstack_controller.api.identity_rest import IdentityRest
from datadog_checks.openstack_controller.api.load_balancer_rest import LoadBalancerRest
from datadog_checks.openstack_controller.api.network_rest import NetworkRest
from datadog_checks.openstack_controller.component_type import ComponentType
from datadog_checks.openstack_controller.http_error import ComponentNotFoundError, http_auth
from datadog_checks.openstack_controller.metrics import (
    KEYSTONE_DOMAINS_METRICS,
    KEYSTONE_DOMAINS_METRICS_PREFIX,
    KEYSTONE_GROUPS_METRICS,
    KEYSTONE_GROUPS_METRICS_PREFIX,
    KEYSTONE_LIMITS_METRICS,
    KEYSTONE_LIMITS_METRICS_PREFIX,
    KEYSTONE_PROJECTS_METRICS,
    KEYSTONE_PROJECTS_METRICS_PREFIX,
    KEYSTONE_SERVICES_METRICS,
    KEYSTONE_SERVICES_METRICS_PREFIX,
    KEYSTONE_USERS_METRICS,
    KEYSTONE_USERS_METRICS_PREFIX,
    NOVA_FLAVORS_METRICS,
    NOVA_FLAVORS_METRICS_PREFIX,
    NOVA_HYPERVISOR_METRICS,
    NOVA_HYPERVISOR_METRICS_PREFIX,
    NOVA_LIMITS_METRICS,
    NOVA_METRICS_PREFIX,
    NOVA_QUOTA_SETS_METRICS,
    NOVA_SERVER_METRICS,
    NOVA_SERVER_METRICS_PREFIX,
    NOVA_SERVICES_METRICS,
    NOVA_SERVICES_METRICS_PREFIX,
    get_normalized_metrics,
)


class ApiRest(Api):
    def __init__(self, config, logger, http):
        super(ApiRest, self).__init__()
        self.log = logger
        self.config = config
        self.http = http
        self._identity_component = IdentityRest(self.log, self.http, '{}/v3'.format(self.config.keystone_server_url))
        self._catalog = {}
        self._components = {}
        self._endpoints = {}
        self._add_microversion_headers()
        self._current_project_id = None
        self._called_endpoints = []

    def component_in_catalog(self, component_type):
        if self._catalog:
            for item in self._catalog:
                if item['type'] == component_type:
                    return True
        return False

    def set_current_project(self, project_id):
        self._current_project_id = project_id

    def _add_microversion_headers(self):
        if self.config.nova_microversion:
            self.log.debug("adding X-OpenStack-Nova-API-Version header to `%s`", self.config.nova_microversion)
            self.http.options['headers']['X-OpenStack-Nova-API-Version'] = self.config.nova_microversion

        if self.config.ironic_microversion:
            self.log.debug("adding X-OpenStack-Ironic-API-Version header to `%s`", self.config.ironic_microversion)
            self.http.options['headers']['X-OpenStack-Ironic-API-Version'] = self.config.ironic_microversion

    def get_response_time(self, endpoint_type):
        endpoint = self._get_endpoint(endpoint_type)
        self.log.debug("%s endpoint: %s", endpoint_type.value, endpoint)
        if endpoint not in self._called_endpoints:
            response = self.http.get(endpoint)
            response.raise_for_status()
            self._called_endpoints.append(endpoint)
            self.log.debug("response: %s", response.json())
            return response.elapsed.total_seconds() * 1000
        else:
            self.log.debug("%s already called", endpoint)
        return None

    def get_identity_domains(self):
        self.log.debug("getting identity domains")
        domains_endpoint = '{}/v3/domains'.format(self._get_endpoint(ComponentType.IDENTITY))
        if domains_endpoint not in self._called_endpoints:
            self.log.debug("domains_endpoint: %s", domains_endpoint)
            response = self.http.get(domains_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(domains_endpoint)
            self.log.debug("response: %s", response.json())
            domain_metrics = {}
            for domain in response.json()['domains']:
                domain_metrics[domain['id']] = {
                    'name': domain['name'],
                    'tags': domain['tags'],
                    'metrics': get_normalized_metrics(
                        domain, KEYSTONE_DOMAINS_METRICS_PREFIX, KEYSTONE_DOMAINS_METRICS
                    ),
                }
            return domain_metrics
        return None

    def get_identity_projects(self):
        self.log.debug("getting identity projects")
        projects_endpoint = '{}/v3/projects'.format(self._get_endpoint(ComponentType.IDENTITY))
        if projects_endpoint not in self._called_endpoints:
            self.log.debug("projects_endpoint: %s", projects_endpoint)
            response = self.http.get(projects_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(projects_endpoint)
            self.log.debug("response: %s", response.json())
            project_metrics = {}
            for project in response.json()['projects']:
                project_metrics[project['id']] = {
                    'name': project['name'],
                    'domain_id': project['domain_id'],
                    'tags': project['tags'],
                    'metrics': get_normalized_metrics(
                        project, KEYSTONE_PROJECTS_METRICS_PREFIX, KEYSTONE_PROJECTS_METRICS
                    ),
                }
            return project_metrics
        return None

    def get_identity_users(self):
        self.log.debug("getting identity users")
        users_endpoint = '{}/v3/users'.format(self._get_endpoint(ComponentType.IDENTITY))
        if users_endpoint not in self._called_endpoints:
            self.log.debug("users_endpoint: %s", users_endpoint)
            response = self.http.get(users_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(users_endpoint)
            self.log.debug("response: %s", response.json())
            user_metrics = {}
            for user in response.json()['users']:
                user_metrics[user['id']] = {
                    'name': user['name'],
                    'domain_id': user['domain_id'],
                    'metrics': get_normalized_metrics(user, KEYSTONE_USERS_METRICS_PREFIX, KEYSTONE_USERS_METRICS),
                }
            return user_metrics
        return None

    def get_identity_groups(self):
        self.log.debug("getting identity groups")
        groups_endpoint = '{}/v3/groups'.format(self._get_endpoint(ComponentType.IDENTITY))
        if groups_endpoint not in self._called_endpoints:
            self.log.debug("groups_endpoint: %s", groups_endpoint)
            response = self.http.get(groups_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(groups_endpoint)
            self.log.debug("response: %s", response.json())
            groups_metrics = {}
            for group in response.json()['groups']:
                groups_metrics[group['id']] = {
                    'name': group['name'],
                    'domain_id': group['domain_id'],
                    'metrics': get_normalized_metrics(group, KEYSTONE_GROUPS_METRICS_PREFIX, KEYSTONE_GROUPS_METRICS),
                }
            return groups_metrics
        return None

    def get_identity_group_users(self, group_id):
        self.log.debug("getting identity group users")
        group_users_endpoint = '{}/v3/groups/{}/users'.format(self._get_endpoint(ComponentType.IDENTITY), group_id)
        self.log.debug("group_users_endpoint: %s", group_users_endpoint)
        response = self.http.get(group_users_endpoint)
        response.raise_for_status()
        self._called_endpoints.append(group_users_endpoint)
        self.log.debug("response: %s", response.json())
        group_users = {}
        for user in response.json()['users']:
            group_users[user['id']] = {
                'name': user['name'],
            }
        return group_users

    def get_identity_services(self):
        self.log.debug("getting identity services")
        services_endpoint = '{}/v3/services'.format(self._get_endpoint(ComponentType.IDENTITY))
        if services_endpoint not in self._called_endpoints:
            self.log.debug("services_endpoint: %s", services_endpoint)
            response = self.http.get(services_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(services_endpoint)
            self.log.debug("response: %s", response.json())
            service_metrics = {}
            for service in response.json()['services']:
                service_metrics[service['id']] = {
                    'name': service['name'],
                    'type': service['type'],
                    'metrics': get_normalized_metrics(
                        service, KEYSTONE_SERVICES_METRICS_PREFIX, KEYSTONE_SERVICES_METRICS
                    ),
                }
            return service_metrics
        return None

    def get_identity_limits(self):
        self.log.debug("getting identity limits")
        registered_limits_endpoint = '{}/v3/registered_limits'.format(self._get_endpoint(ComponentType.IDENTITY))
        identity_limits = None
        if registered_limits_endpoint not in self._called_endpoints:
            self.log.debug("registered_limits_endpoint: %s", registered_limits_endpoint)
            response = self.http.get(registered_limits_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(registered_limits_endpoint)
            self.log.debug("response: %s", response.json())
            identity_limits = {}
            for registered_limit in response.json()['registered_limits']:
                identity_limits[registered_limit['id']] = {
                    'resource_name': registered_limit['resource_name'],
                    'service_id': registered_limit['service_id'],
                    'region_id': registered_limit['region_id'],
                    'metrics': get_normalized_metrics(
                        registered_limit,
                        KEYSTONE_LIMITS_METRICS_PREFIX,
                        KEYSTONE_LIMITS_METRICS,
                        lambda key: 'limit' if key == 'default_limit' else key,
                    ),
                }
        limits_endpoint = '{}/v3/limits'.format(self._get_endpoint(ComponentType.IDENTITY))
        if limits_endpoint not in self._called_endpoints:
            self.log.debug("limits_endpoint: %s", limits_endpoint)
            response = self.http.get(limits_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(limits_endpoint)
            self.log.debug("response: %s", response.json())
            for limit in response.json()['limits']:
                identity_limits[limit['id']] = {
                    'resource_name': limit.get('resource_name'),
                    'service_id': limit.get('service_id'),
                    'region_id': limit.get('region_id'),
                    'domain_id': limit.get('domain_id'),
                    'project_id': limit.get('project_id'),
                    'metrics': get_normalized_metrics(
                        limit,
                        KEYSTONE_LIMITS_METRICS_PREFIX,
                        KEYSTONE_LIMITS_METRICS,
                        {'resource_limit': 'limit'},
                    ),
                }
        return identity_limits

    def get_compute_limits(self):
        self.log.debug("getting compute limits")
        limits_endpoint = '{}/limits'.format(self._get_endpoint(ComponentType.COMPUTE))
        if limits_endpoint not in self._called_endpoints:
            self.log.debug("limits_endpoint: %s", limits_endpoint)
            response = self.http.get(limits_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(limits_endpoint)
            self.log.debug("response: %s", response.json())
            return get_normalized_metrics(response.json(), NOVA_METRICS_PREFIX, NOVA_LIMITS_METRICS)
        return None

    def get_compute_services(self):
        self.log.debug("getting compute services")
        services_endpoint = '{}/os-services'.format(self._get_endpoint(ComponentType.COMPUTE))
        if services_endpoint not in self._called_endpoints:
            self.log.debug("services_endpoint: %s", services_endpoint)
            response = self.http.get(services_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(services_endpoint)
            self.log.debug("response: %s", response.json())
            compute_services = {}
            for service in response.json()['services']:
                compute_services[service['id']] = {
                    'name': service['binary'].replace('-', '_'),
                    'zone': service['zone'],
                    'host': service['host'],
                    'status': service['status'],
                    'state': service['state'],
                    'metrics': get_normalized_metrics(
                        service,
                        NOVA_SERVICES_METRICS_PREFIX,
                        NOVA_SERVICES_METRICS,
                        lambda key: 'up' if key == 'state' else key,
                        lambda key, value: int(value == 'up') if key == 'state' else value,
                    ),
                }
            return compute_services
        return None

    def get_compute_flavors(self):
        self.log.debug("getting compute flavors")
        flavors_endpoint = '{}/flavors/detail'.format(self._get_endpoint(ComponentType.COMPUTE))
        if flavors_endpoint not in self._called_endpoints:
            self.log.debug("flavors_endpoint: %s", flavors_endpoint)
            response = self.http.get(flavors_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(flavors_endpoint)
            self.log.debug("response: %s", response.json())
            compute_flavors = {}
            for flavor in response.json()['flavors']:
                compute_flavors[flavor['id']] = {
                    'name': flavor['name'],
                    'metrics': get_normalized_metrics(
                        flavor,
                        NOVA_FLAVORS_METRICS_PREFIX,
                        NOVA_FLAVORS_METRICS,
                        value_lambda=lambda key, value: int(value or 0) if key == 'swap' else value,
                    ),
                }
            return compute_flavors
        return None

    def get_compute_hypervisors(self):
        self.log.debug("getting compute flavors")
        hypervisors_endpoint = '{}/os-hypervisors/detail?with_servers=true'.format(
            self._get_endpoint(ComponentType.COMPUTE)
        )
        if hypervisors_endpoint not in self._called_endpoints:
            self.log.debug("hypervisors_endpoint: %s", hypervisors_endpoint)
            response = self.http.get(hypervisors_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(hypervisors_endpoint)
            self.log.debug("response: %s", response.json())
            compute_hypervisors = {}
            for hypervisor in response.json()['hypervisors']:
                hypervisor_type = hypervisor['hypervisor_type']
                compute_hypervisors[hypervisor['id']] = {
                    'name': hypervisor['hypervisor_hostname'],
                    'state': hypervisor.get('state'),
                    'type': hypervisor_type,
                    'status': hypervisor['status'],
                    'metrics': get_normalized_metrics(
                        hypervisor,
                        NOVA_HYPERVISOR_METRICS_PREFIX,
                        NOVA_HYPERVISOR_METRICS,
                    ),
                }
            return compute_hypervisors
        return None

    def get_compute_os_aggregates(self):
        self.log.debug("getting compute os-aggregates")
        os_aggregates_endpoint = '{}/os-aggregates'.format(self._get_endpoint(ComponentType.COMPUTE))
        if os_aggregates_endpoint not in self._called_endpoints:
            self.log.debug("os_aggregates_endpoint: %s", os_aggregates_endpoint)
            response = self.http.get(os_aggregates_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(os_aggregates_endpoint)
            self.log.debug("response: %s", response.json())
            compute_os_aggregates = {}
            for aggregate in response.json()['aggregates']:
                compute_os_aggregates[str(aggregate['id'])] = {
                    'name': aggregate['name'],
                    'availability_zone': aggregate['availability_zone'],
                    'hosts': aggregate['hosts'],
                }
            return compute_os_aggregates
        return None

    def get_compute_quota_sets(self, project_id):
        self.log.debug("getting compute quota sets")
        quota_sets_endpoint = '{}/os-quota-sets/{}'.format(self._get_endpoint(ComponentType.COMPUTE), project_id)
        if quota_sets_endpoint not in self._called_endpoints:
            self.log.debug("quota_sets_endpoint: %s", quota_sets_endpoint)
            response = self.http.get(quota_sets_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(quota_sets_endpoint)
            self.log.debug("response: %s", response.json())
            quota_sets = {}
            quota_sets[response.json()['quota_set']['id']] = {
                'metrics': get_normalized_metrics(response.json(), NOVA_METRICS_PREFIX, NOVA_QUOTA_SETS_METRICS),
            }
            return quota_sets
        return None

    def get_compute_servers(self, project_id):
        self.log.debug("getting compute servers")
        servers_endpoint = '{}/servers/detail?project_id={}'.format(
            self._get_endpoint(ComponentType.COMPUTE), project_id
        )
        if servers_endpoint not in self._called_endpoints:
            self.log.debug("servers_endpoint: %s", servers_endpoint)
            response = self.http.get(servers_endpoint)
            response.raise_for_status()
            self._called_endpoints.append(servers_endpoint)
            self.log.debug("response: %s", response.json())
            server_metrics = {}
            for server in response.json()['servers']:
                server_metrics[server['id']] = {
                    'name': server['name'],
                    'status': server['status'].lower(),
                    'hypervisor_hostname': server.get('OS-EXT-SRV-ATTR:hypervisor_hostname'),
                    'instance_hostname': server.get('OS-EXT-SRV-ATTR:hostname'),
                    'metrics': get_normalized_metrics(server, NOVA_SERVER_METRICS_PREFIX, NOVA_SERVER_METRICS),
                }
                server_flavor = self._get_server_flavor(server.get('flavor'))
                self.log.debug("server_flavor: %s", server_flavor)
                self.log.debug("server_metrics[server['id']]: %s", server_metrics[server['id']])
                server_metrics[server['id']].update(server_flavor)
            return server_metrics
        return None

    def _get_server_flavor(self, flavor):
        server_flavor = {}
        if flavor:
            flavor_id = flavor.get('id')
            if flavor_id is not None:
                flavor_metrics = self._get_flavor_id(flavor_id)
                server_flavor['flavor_name'] = flavor_metrics[flavor_id]['name']
                server_flavor['metrics'] = get_normalized_metrics(
                    flavor_metrics[flavor_id]['metrics'],
                    f'{NOVA_SERVER_METRICS_PREFIX}.flavor',
                    NOVA_SERVER_METRICS,
                )
            else:
                server_flavor['flavor_name'] = flavor.get('original_name')
                server_flavor['metrics'].update(
                    get_normalized_metrics(flavor, f'{NOVA_SERVER_METRICS_PREFIX}.flavor', NOVA_SERVER_METRICS)
                )
        return server_flavor

    def _get_flavor_id(self, flavor_id):
        response = self.http.get('{}/flavors/{}'.format(self._get_endpoint(ComponentType.COMPUTE), flavor_id))
        response.raise_for_status()
        self.log.debug("response: %s", response.json())
        flavor_metrics = {}
        flavor = response.json()['flavor']
        flavor_metrics[flavor['id']] = {'name': flavor['name'], 'metrics': {}}
        for key, value in flavor.items():
            metric_key = re.sub(r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1', key).lower().replace("-", "_")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                flavor_metrics[flavor['id']]['metrics'][metric_key] = value
            elif isinstance(value, str):
                try:
                    flavor_metrics[flavor['id']]['metrics'][metric_key] = int(value) if value else 0
                except ValueError:
                    pass
        return flavor_metrics

    def get_auth_projects(self):
        self.log.debug("getting auth projects")
        auth_projects_endpoint = '{}/v3/auth/projects'.format(self.config.keystone_server_url)
        self.log.debug("auth_projects_endpoint: %s", auth_projects_endpoint)
        response = self.http.get(auth_projects_endpoint)
        response.raise_for_status()
        self.log.debug("response: %s", response.json())
        return [{'id': project['id'], 'name': project['name']} for project in response.json()['projects']]

    def get_block_storage_response_time(self):
        self.log.debug("getting block-storage response time")
        component = self._get_component(ComponentType.BLOCK_STORAGE)
        if component:
            return component.get_response_time()
        return None

    def get_load_balancer_loadbalancers(self, project_id):
        self.log.debug("getting load-balancer loadbalancers")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_loadbalancers(project_id)
        return None

    def get_load_balancer_listeners(self, project_id):
        self.log.debug("getting load-balancer listeners")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_listeners(project_id)
        return None

    def get_load_balancer_pools(self, project_id):
        self.log.debug("getting load-balancer pools")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_pools(project_id)
        return None

    def get_load_balancer_members_by_pool(self, project_id, pool_id):
        self.log.debug("getting load-balancer members by pool")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_members_by_pool(pool_id, project_id)
        return None

    def get_load_balancer_healthmonitors(self, project_id):
        self.log.debug("getting load-balancer healthmonitors")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_healthmonitors(project_id)
        return None

    def get_load_balancer_loadbalancer_statistics(self, project_id, loadbalancer_id):
        self.log.debug("getting load-balancer loadbalancer statistics")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_loadbalancer_statistics(loadbalancer_id)
        return None

    def get_load_balancer_listener_statistics(self, project_id, listener_id):
        self.log.debug("getting load-balancer listener statistics")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_listener_statistics(listener_id)
        return None

    def get_load_balancer_listeners_by_loadbalancer(self, project_id, loadbalancer_id):
        self.log.debug("getting load-balancer listeners by loadbalancer")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_listeners_by_loadbalancer(loadbalancer_id, project_id)
        return None

    def get_load_balancer_pools_by_loadbalancer(self, project_id, loadbalancer_id):
        self.log.debug("getting load-balancer pools by loadbalancer")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_pools_by_loadbalancer(loadbalancer_id, project_id)
        return None

    def get_load_balancer_healthmonitors_by_pool(self, project_id, pool_id):
        self.log.debug("getting load-balancer healthmonitors by pool")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_healthmonitors_by_pool(pool_id, project_id)
        return None

    def get_load_balancer_amphorae(self, project_id):
        self.log.debug("getting load-balancer amphorae")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_amphorae()
        return None

    def get_load_balancer_amphorae_by_loadbalancer(self, project_id, loadbalancer_id):
        self.log.debug("getting load-balancer amphorae by loadbalancer")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_amphorae_by_loadbalancer(loadbalancer_id)
        return None

    def get_load_balancer_amphora_statistics(self, project_id, amphora_id):
        self.log.debug("getting load-balancer amphora statistics")
        component = self._get_component(ComponentType.LOAD_BALANCER)
        if component:
            return component.get_amphora_statistics(amphora_id)
        return None

    # def get_compute_limits(self):
    #     self.log.debug("getting compute limits")
    #     component = self._get_component(ComponentType.COMPUTE)
    #     if component:
    #         return component.get_limits()
    #     return None

    @http_auth()
    def get_compute_quota_set(self, project_id):
        self.log.debug("getting compute quotas")
        component = self._get_component(ComponentType.COMPUTE)
        if component:
            return component.get_quota_set(project_id)
        return None

    # def get_compute_services(self):
    #     self.log.debug("getting compute services")
    #     component = self._get_component(ComponentType.COMPUTE)
    #     if component:
    #         return component.get_services()
    #     return None

    # @http_auth()
    # def get_compute_servers(self, project_id):
    #     self.log.debug("getting compute servers")
    #     component = self._get_component(ComponentType.COMPUTE)
    #     if component:
    #         return component.get_servers(project_id)
    #     return None

    # def get_compute_flavors(self):
    #     self.log.debug("getting compute flavors")
    #     component = self._get_component(ComponentType.COMPUTE)
    #     if component:
    #         return component.get_flavors()
    #     return None

    # def get_compute_hypervisors(self):
    #     self.log.debug("getting compute hypervisors")
    #     component = self._get_component(ComponentType.COMPUTE)
    #     if component:
    #         return component.get_hypervisors()
    #     return None

    # def get_compute_os_aggregates(self):
    #     self.log.debug("getting compute os-aggregates")
    #     component = self._get_component(ComponentType.COMPUTE)
    #     if component:
    #         return component.get_os_aggregates()
    #     return None

    def get_network_quotas(self, project_id):
        self.log.debug("getting network quotas")
        component = self._get_component(ComponentType.NETWORK)
        if component:
            return component.get_quotas(project_id)
        return None

    def get_baremetal_nodes(self):
        self.log.debug("getting baremetal nodes")
        component = self._get_component(ComponentType.BAREMETAL)
        if component:
            return component.get_nodes()
        return None

    def get_baremetal_conductors(self):
        self.log.debug("getting baremetal conductors")
        component = self._get_component(ComponentType.BAREMETAL)
        if component and component.collect_conductor_metrics():
            return component.get_conductors()
        else:
            self.log.info(
                "Ironic conductors metrics are not available. "
                "Please specify an `ironic_microversion` greater than 1.49 to recieve these metrics"
            )
            return None

    def get_network_agents(self):
        self.log.debug("getting network agents")
        component = self._get_component(ComponentType.NETWORK)
        if component:
            return component.get_agents()
        return None

    def authorize(self):
        self._catalog = {}
        self._components = {}
        self._endpoints = {}
        scope = {"project": {"id": self._current_project_id}} if self._current_project_id else "unscoped"
        data = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.config.username,
                            "password": self.config.password,
                            "domain": {"id": self.config.domain_id},
                        }
                    },
                },
                "scope": scope,
            }
        }
        auth_tokens_endpoint = '{}/v3/auth/tokens'.format(self.config.keystone_server_url)
        self.log.debug("auth_tokens_endpoint: %s", auth_tokens_endpoint)
        self.log.debug("data: %s", data)
        response = self.http.post(auth_tokens_endpoint, json=data)
        response.raise_for_status()
        self.log.debug("response: %s", response.json())
        self._catalog = response.json().get('token', {}).get('catalog', {})
        self.http.options['headers']['X-Auth-Token'] = response.headers['X-Subject-Token']

    def _get_component(self, endpoint_type):
        if endpoint_type in self._components:
            self.log.debug("cached component of type %s", endpoint_type)
            return self._components[endpoint_type]
        endpoint = self._get_endpoint(endpoint_type)
        if endpoint:
            self._components[endpoint_type] = self._make_component(endpoint_type, endpoint)
            return self._components[endpoint_type]
        return None

    def _get_endpoint(self, endpoint_type):
        endpoint_interface = 'internal' if self.config.use_internal_endpoints else 'public'
        if endpoint_type in self._endpoints:
            self.log.debug("cached endpoint of type %s", endpoint_type)
            return self._endpoints[endpoint_type]
        for item in self._catalog:
            if item['type'] == endpoint_type:
                for endpoint in item['endpoints']:
                    if endpoint['interface'] == endpoint_interface:
                        self._endpoints[endpoint_type] = endpoint['url']
                        return self._endpoints[endpoint_type]
        raise ComponentNotFoundError

    def _make_component(self, endpoint_type, endpoint):
        if endpoint_type == ComponentType.IDENTITY:
            return IdentityRest(self.log, self.http, endpoint)
        elif endpoint_type == ComponentType.COMPUTE:
            return ComputeRest(self.log, self.http, endpoint)
        elif endpoint_type == ComponentType.NETWORK:
            return NetworkRest(self.log, self.http, endpoint)
        elif endpoint_type == ComponentType.BLOCK_STORAGE:
            return BlockStorageRest(self.log, self.http, endpoint)
        elif endpoint_type == ComponentType.BAREMETAL:
            return BaremetalRest(self.log, self.http, endpoint, self.config.ironic_microversion)
        elif endpoint_type == ComponentType.LOAD_BALANCER:
            return LoadBalancerRest(self.log, self.http, endpoint)
        return None
