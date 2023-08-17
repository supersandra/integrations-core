# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import logging

import mock
import pytest

from datadog_checks.base import AgentCheck
from datadog_checks.dev.http import MockResponse
from datadog_checks.openstack_controller import OpenStackControllerCheck

from .common import MockHttp

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'replace': {
                    'identity/v3/auth/tokens': lambda d: {
                        **d,
                        **{
                            'token': {
                                **d['token'],
                                **{'catalog': []},
                            }
                        },
                    }
                },
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_not_in_catalog(aggregator, dd_run_check, instance, caplog, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.response_time',
        count=0,
    )
    aggregator.assert_service_check(
        'openstack.keystone.api.up',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity' not in args_list
    assert '`identity` component not found in catalog' in caplog.text


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_response_time_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.response_time',
        count=0,
    )
    aggregator.assert_service_check(
        'openstack.keystone.api.up',
        status=AgentCheck.CRITICAL,
        tags=[
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_response_time(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.response_time',
        count=1,
        tags=[
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )
    aggregator.assert_service_check(
        'openstack.keystone.api.up',
        status=AgentCheck.OK,
        tags=[
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/domains': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_domains_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.domains.count',
        count=0,
    )
    aggregator.assert_metric(
        'openstack.keystone.domains.enabled',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/domains' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/domains': MockResponse(json_data={"domains": []}, status_code=200)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_domains_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.domains.count',
        value=0,
        count=1,
        tags=['keystone_server:http://127.0.0.1:8080/identity'],
    )
    aggregator.assert_metric(
        'openstack.keystone.domains.enabled',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/domains' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_domains_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.domains.count',
        value=2,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.domains.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'domain_name:Default',
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.domains.enabled',
        value=1,
        tags=[
            'domain_id:03e40b01788d403e98e4b9a20210492e',
            'domain_name:New domain',
            'keystone_server:http://127.0.0.1:8080/identity',
            'foo',
            'bar',
        ],
    )


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/projects': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_projects_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.projects.count',
        count=0,
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/projects' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/projects': MockResponse(json_data={"projects": []}, status_code=200)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_projects_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.projects.count',
        value=0,
        count=1,
        tags=['keystone_server:http://127.0.0.1:8080/identity'],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/projects' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_projects_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.projects.count',
        value=5,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:1e6e233e637d4d55a50a62b63398ad15',
            'project_name:demo',
            'foo',
            'bar',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:6e39099cccde4f809b003d9e0dd09304',
            'project_name:admin',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:b0700d860b244dcbb038541976cd8f32',
            'project_name:alt_demo',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=0,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:c1147335eac0402ea9cabaae59c267e1',
            'project_name:invisible_to_admin',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:e9e405ed5811407db982e3113e52d26b',
            'project_name:service',
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/projects' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/users': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_users_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.users.count',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/users' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/users': MockResponse(json_data={"users": []}, status_code=200)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_users_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.users.count',
        value=0,
        count=1,
        tags=['keystone_server:http://127.0.0.1:8080/identity'],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/users' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_users_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.users.count',
        value=13,
        tags=['keystone_server:http://127.0.0.1:8080/identity'],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:78205c506b534738bc851d3e189a00c3',
            'user_name:admin',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:2059bc7347c94546bef812b1092cc5cf',
            'user_name:demo',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=0,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:e3e3e90d24b34e52970a54c9e8656778',
            'user_name:demo_reader',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:3472440960de4595be3b975d230979d3',
            'user_name:alt_demo',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:87e289ddac6d4dce8626a659c5ea88ae',
            'user_name:alt_demo_member',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:61f0cd4dec604f968ff6cc92d4c1c278',
            'user_name:alt_demo_reader',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:5d0c9a6896c9430b8a1528424c9ee6f6',
            'user_name:system_member',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:aeaa8e9835284e4380583e10bb2575fd',
            'user_name:system_reader',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:bc603ecd6ed940119be9a3a933c39509',
            'user_name:nova',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:ad9f72f911744acbbf69379e45a3ef37',
            'user_name:glance',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:94fb5df1e547496894f9304a9b4a06d4',
            'user_name:neutron',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:af4653d4f2dc4a38b8af36cbd3993d5a',
            'user_name:cinder',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.users.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'user_id:fc7c3571bed548e98e7df266f57a50f7',
            'user_name:placement',
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/users' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/groups': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_groups_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.groups.count',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/groups' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {
                    'identity/v3/groups/89b36a4c32c44b0ea8856b6357f101ea/users': MockResponse(status_code=500)
                },
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_group_users_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.groups.count',
        value=2,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'domain_id:default',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.groups.users',
        count=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'domain_id:default',
            'group_id:89b36a4c32c44b0ea8856b6357f101ea',
            'group_name:admins',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.groups.users',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'domain_id:default',
            'group_id:9acda6caf16e4828935f4f681ee8b3e5',
            'group_name:nonadmins',
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/groups' in args_list
    assert 'http://10.164.0.11/identity/v3/groups/89b36a4c32c44b0ea8856b6357f101ea/users' in args_list
    assert 'http://10.164.0.11/identity/v3/groups/9acda6caf16e4828935f4f681ee8b3e5/users' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/groups': MockResponse(json_data={"groups": []}, status_code=200)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_groups_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.groups.count',
        value=0,
        count=1,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'domain_id:default',
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/groups' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_groups_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.groups.count',
        value=2,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'domain_id:default',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.groups.users',
        value=1,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'domain_id:default',
            'group_id:89b36a4c32c44b0ea8856b6357f101ea',
            'group_name:admins',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.groups.users',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'domain_id:default',
            'group_id:9acda6caf16e4828935f4f681ee8b3e5',
            'group_name:nonadmins',
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/groups' in args_list
    assert 'http://10.164.0.11/identity/v3/groups/89b36a4c32c44b0ea8856b6357f101ea/users' in args_list
    assert 'http://10.164.0.11/identity/v3/groups/9acda6caf16e4828935f4f681ee8b3e5/users' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/services': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_services_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.services.count',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/services' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/projects': MockResponse(json_data={"projects": []}, status_code=200)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_services_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.projects.count',
        value=0,
        count=1,
        tags=['keystone_server:http://127.0.0.1:8080/identity'],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/projects' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_services_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:1e6e233e637d4d55a50a62b63398ad15',
            'project_name:demo',
            'foo',
            'bar',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:6e39099cccde4f809b003d9e0dd09304',
            'project_name:admin',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:b0700d860b244dcbb038541976cd8f32',
            'project_name:alt_demo',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=0,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:c1147335eac0402ea9cabaae59c267e1',
            'project_name:invisible_to_admin',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.projects.enabled',
        value=1,
        tags=[
            'domain_id:default',
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:e9e405ed5811407db982e3113e52d26b',
            'project_name:service',
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/projects' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/registered_limits': MockResponse(status_code=500)},
            },
            id='registered_limits',
        ),
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/limits': MockResponse(status_code=500)},
            },
            id='limits',
        ),
    ],
    indirect=['mock_api_rest'],
)
def test_limits_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.limits.count',
        count=0,
    )


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {
                    'identity/v3/registered_limits': MockResponse(json_data={"registered_limits": []}, status_code=200),
                    'identity/v3/limits': MockResponse(json_data={"limits": []}, status_code=200),
                },
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_limits_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.limits.count',
        value=0,
        count=1,
        tags=['keystone_server:http://127.0.0.1:8080/identity'],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/registered_limits' in args_list
    assert 'http://10.164.0.11/identity/v3/limits' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_limits_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.keystone.limits.count',
        value=4,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.limits.limit',
        value=1000,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'limit_id:dd4fefa5602a4414b1c0a01ac7514b97',
            'resource_name:image_size_total',
            'service_id:82624ab61fb04f058d043facf315fa3c',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.limits.limit',
        value=1000,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'limit_id:5e7d44c9d30d47919187a5c1a58a8885',
            'resource_name:image_stage_total',
            'service_id:82624ab61fb04f058d043facf315fa3c',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.limits.limit',
        value=100,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'limit_id:9f489d63900841f4a70fe58036c81339',
            'resource_name:image_count_total',
            'service_id:82624ab61fb04f058d043facf315fa3c',
        ],
    )
    aggregator.assert_metric(
        'openstack.keystone.limits.limit',
        value=100,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'limit_id:5d26b57b414c4e25848cd34b38f56606',
            'resource_name:image_count_uploading',
            'service_id:82624ab61fb04f058d043facf315fa3c',
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/identity/v3/registered_limits' in args_list
    assert 'http://10.164.0.11/identity/v3/limits' in args_list
