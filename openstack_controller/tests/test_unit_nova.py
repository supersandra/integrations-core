# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import logging

import mock
import pytest

from datadog_checks.base import AgentCheck
from datadog_checks.dev.http import MockResponse
from datadog_checks.openstack_controller import OpenStackControllerCheck
from datadog_checks.openstack_controller.metrics import (
    NOVA_HYPERVISOR_METRICS,
    NOVA_LIMITS_METRICS,
    NOVA_QUOTA_SETS_METRICS,
    NOVA_SERVER_METRICS,
    NOVA_SERVICE_CHECK,
)

from .common import CONFIG, CONFIG_NOVA_MICROVERSION_LATEST, MockHttp, check_microversion, is_mandatory

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
        'openstack.nova.response_time',
        count=0,
    )
    aggregator.assert_service_check(
        'openstack.nova.api.up',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1' not in args_list
    assert '`compute` component not found in catalog' in caplog.text


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'compute/v2.1': MockResponse(status_code=500)},
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
        'openstack.nova.response_time',
        count=0,
    )
    aggregator.assert_service_check(
        'openstack.nova.api.up',
        status=AgentCheck.CRITICAL,
        tags=[
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1' in args_list


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
        'openstack.nova.response_time',
        count=1,
        tags=[
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )
    aggregator.assert_service_check(
        'openstack.nova.api.up',
        status=AgentCheck.OK,
        tags=[
            'keystone_server:{}'.format(instance["keystone_server_url"]),
        ],
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'compute/v2.1/limits': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_limits_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_total_instances',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/limits' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {
                    'compute/v2.1/limits': MockResponse(
                        json_data={"limits": {"rate": [], "absolute": {}}}, status_code=200
                    )
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
        'openstack.nova.limits.absolute.max_total_instances',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/limits' in args_list


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
        'openstack.nova.limits.absolute.max_total_instances',
        value=10,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_total_cores',
        value=20,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_total_ram_size',
        value=51200,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_server_meta',
        value=128,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_image_meta',
        value=128,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_personality',
        value=5,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_personality_size',
        value=10240,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_total_keypairs',
        value=100,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_server_groups',
        value=10,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_server_group_members',
        value=10,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_total_floating_ips',
        value=-1,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_security_groups',
        value=-1,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.max_security_group_rules',
        value=-1,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.total_ram_used',
        value=2048,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.total_cores_used',
        value=8,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.total_instances_used',
        value=8,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.total_floating_ips_used',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.total_security_groups_used',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.limits.absolute.total_server_groups_used',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
        ],
    )


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'compute/v2.1/os-services': MockResponse(status_code=500)},
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
        'openstack.nova.service.up',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/os-services' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'compute/v2.1/os-services': MockResponse(json_data={"services": []}, status_code=200)},
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
        'openstack.nova.service.up',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/os-services' in args_list


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
        'openstack.nova.service.up',
        count=4,
    )


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'compute/v2.1/flavors/detail': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_flavors_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.flavor.vcpus',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/flavors/detail' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'compute/v2.1/flavors/detail': MockResponse(json_data={"flavors": []}, status_code=200)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_flavors_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.flavor.vcpus',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/os-services' in args_list


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
def test_flavors_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.flavor.vcpus',
        count=12,
    )


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'compute/v2.1/os-hypervisors/detail?with_servers=true': MockResponse(status_code=500)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_hypervisors_exception(aggregator, dd_run_check, instance, caplog, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.hypervisor.current_workload',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/os-hypervisors/detail?with_servers=true' in args_list
    assert 'Exception while getting compute hypervisors' in caplog.text


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {
                    'compute/v2.1/os-hypervisors/detail?with_servers=true': MockResponse(
                        json_data={"hypervisors": []}, status_code=200
                    )
                },
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_hypervisors_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.hypervisor.current_workload',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/os-hypervisors/detail?with_servers=true' in args_list


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
def test_hypervisors_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.hypervisor.current_workload',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.disk_available_least',
        value=59,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.free_disk_gb',
        value=96,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.free_ram_mb',
        value=11406,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.local_gb',
        value=96,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.local_gb_used',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.memory_mb',
        value=14990,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.memory_mb_used',
        value=3584,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.running_vms',
        value=12,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.vcpus',
        value=4,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.vcpus_used',
        value=12,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.hypervisor.up',
        value=1,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'hypervisor_id:1',
            'hypervisor:agent-integrations-openstack-default',
            'status:enabled',
            'virt_type:QEMU',
            'aggregate:my-aggregate',
            'availability_zone:availability-zone',
        ],
    )


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {
                    'compute/v2.1/os-quota-sets/1e6e233e637d4d55a50a62b63398ad15': MockResponse(status_code=500),
                    'compute/v2.1/os-quota-sets/6e39099cccde4f809b003d9e0dd09304': MockResponse(status_code=500),
                },
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_os_quota_sets_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.quota_set.cores',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/os-quota-sets/1e6e233e637d4d55a50a62b63398ad15' in args_list
    assert 'http://10.164.0.11/compute/v2.1/os-quota-sets/6e39099cccde4f809b003d9e0dd09304' in args_list


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
def test_os_quota_sets_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.quota_set.cores',
        value=20,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:1e6e233e637d4d55a50a62b63398ad15',
            'project_name:demo',
            'quota_id:1e6e233e637d4d55a50a62b63398ad15',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.quota_set.cores',
        value=20,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:6e39099cccde4f809b003d9e0dd09304',
            'project_name:admin',
            'quota_id:6e39099cccde4f809b003d9e0dd09304',
        ],
    )


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {
                    'compute/v2.1/servers/detail?project_id=1e6e233e637d4d55a50a62b63398ad15': MockResponse(
                        status_code=500
                    ),
                    'compute/v2.1/servers/detail?project_id=6e39099cccde4f809b003d9e0dd09304': MockResponse(
                        status_code=500
                    ),
                },
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_servers_exception(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.server.count',
        count=0,
    )
    args_list = []
    for call in mock_api_rest.get.call_args_list:
        args, kwargs = call
        args_list += list(args)
    assert 'http://10.164.0.11/compute/v2.1/servers/detail?project_id=1e6e233e637d4d55a50a62b63398ad15' in args_list
    assert 'http://10.164.0.11/compute/v2.1/servers/detail?project_id=6e39099cccde4f809b003d9e0dd09304' in args_list


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {
                    'compute/v2.1/servers/detail?project_id=1e6e233e637d4d55a50a62b63398ad15': MockResponse(
                        json_data={"servers": []}, status_code=200
                    ),
                    'compute/v2.1/servers/detail?project_id=6e39099cccde4f809b003d9e0dd09304': MockResponse(
                        json_data={"servers": []}, status_code=200
                    ),
                },
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_servers_empty(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.server.count',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:1e6e233e637d4d55a50a62b63398ad15',
            'project_name:demo',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.server.count',
        value=0,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:6e39099cccde4f809b003d9e0dd09304',
            'project_name:admin',
        ],
    )


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
def test_servers_metrics(aggregator, dd_run_check, instance, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    aggregator.assert_metric(
        'openstack.nova.server.count',
        value=8,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:1e6e233e637d4d55a50a62b63398ad15',
            'project_name:demo',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.server.count',
        value=3,
        tags=[
            'keystone_server:http://127.0.0.1:8080/identity',
            'project_id:6e39099cccde4f809b003d9e0dd09304',
            'project_name:admin',
        ],
    )
    aggregator.assert_metric(
        'openstack.nova.server.active',
        value=1,
        tags=[
            [
                'flavor_name:cirros256',
                'hypervisor:agent-integrations-openstack-default',
                'keystone_server:http://127.0.0.1:8080/identity',
                'project_id:1e6e233e637d4d55a50a62b63398ad15',
                'project_name:demo',
                'server_id:3b27b706-c0ad-4528-a865-7afaf7712130',
                'server_name:demo-2',
                'server_status:active',
            ]
        ],
    )


#
# @pytest.mark.parametrize(
#     "instance",
#     [
#         pytest.param(CONFIG, id="default"),
#         pytest.param(CONFIG_NOVA_MICROVERSION_LATEST, id="latest"),
#     ],
# )
# def test_limits_metrics(aggregator, dd_run_check, monkeypatch, instance):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#     not_found_metrics = []
#     for key, value in NOVA_LIMITS_METRICS.items():
#         if check_microversion(instance, value):
#             if key in aggregator.metric_names:
#                 aggregator.assert_metric(
#                     key,
#                     tags=[
#                         'domain_id:default',
#                         'keystone_server:{}'.format(instance["keystone_server_url"]),
#                     ],
#                 )
#             elif is_mandatory(value):
#                 not_found_metrics.append(key)
#     assert not_found_metrics == [], f"No nova limits metrics found: {not_found_metrics}"
#
#
# @pytest.mark.parametrize(
#     "instance",
#     [
#         pytest.param(CONFIG, id="default"),
#         pytest.param(CONFIG_NOVA_MICROVERSION_LATEST, id="latest"),
#     ],
# )
# def test_quota_set_metrics(aggregator, dd_run_check, monkeypatch, instance):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#     not_found_metrics = []
#     for key, value in NOVA_QUOTA_SETS_METRICS.items():
#         if check_microversion(instance, value):
#             if key in aggregator.metric_names:
#                 aggregator.assert_metric(
#                     key,
#                     tags=[
#                         'domain_id:default',
#                         'keystone_server:{}'.format(instance["keystone_server_url"]),
#                         'project_id:1e6e233e637d4d55a50a62b63398ad15',
#                         'project_name:demo',
#                         'quota_id:1e6e233e637d4d55a50a62b63398ad15',
#                     ],
#                 )
#                 aggregator.assert_metric(
#                     key,
#                     tags=[
#                         'domain_id:default',
#                         'keystone_server:{}'.format(instance["keystone_server_url"]),
#                         'project_id:6e39099cccde4f809b003d9e0dd09304',
#                         'project_name:admin',
#                         'quota_id:6e39099cccde4f809b003d9e0dd09304',
#                     ],
#                 )
#             elif is_mandatory(value):
#                 not_found_metrics.append(key)
#     assert not_found_metrics == [], f"No nova quotas metrics found: {not_found_metrics}"
#
#
# @pytest.mark.parametrize(
#     "instance, has_instance_hostname",
#     [
#         pytest.param(CONFIG, False, id="default"),
#         pytest.param(CONFIG_NOVA_MICROVERSION_LATEST, True, id="latest"),
#     ],
# )
# def test_server_metrics(aggregator, dd_run_check, monkeypatch, instance, has_instance_hostname):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#     not_found_metrics = []
#     for key, value in NOVA_SERVER_METRICS.items():
#         if check_microversion(instance, value):
#             if key in aggregator.metric_names:
#                 if key == "openstack.nova.server.count":
#                     tags = [
#                         'domain_id:default',
#                         'keystone_server:{}'.format(instance["keystone_server_url"]),
#                         'project_id:6e39099cccde4f809b003d9e0dd09304',
#                         'project_name:admin',
#                     ]
#                 else:
#                     tags = [
#                         'domain_id:default',
#                         'keystone_server:{}'.format(instance["keystone_server_url"]),
#                         'project_id:6e39099cccde4f809b003d9e0dd09304',
#                         'project_name:admin',
#                         'server_id:2c653a68-b520-4582-a05d-41a68067d76c',
#                         'server_name:server',
#                         'server_status:active',
#                         'hypervisor:agent-integrations-openstack-default',
#                         'flavor_name:cirros256',
#                     ]
#                     if has_instance_hostname:
#                         tags.append('instance_hostname:server')
#
#                 aggregator.assert_metric(key, tags=tags)
#             elif is_mandatory(value):
#                 not_found_metrics.append(key)
#     assert not_found_metrics == [], f"No nova server metrics found: {not_found_metrics}"
#
#
# @pytest.mark.parametrize(
#     "instance",
#     [
#         pytest.param(CONFIG, id="default"),
#         pytest.param(CONFIG_NOVA_MICROVERSION_LATEST, id="latest"),
#     ],
# )
# def test_flavor_metrics(aggregator, dd_run_check, monkeypatch, instance):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#     not_found_metrics = []
#     for key, value in NOVA_FLAVOR_METRICS.items():
#         if check_microversion(instance, value):
#             if key in aggregator.metric_names:
#                 aggregator.assert_metric(
#                     key,
#                     tags=[
#                         'domain_id:default',
#                         'keystone_server:{}'.format(instance["keystone_server_url"]),
#                         'flavor_id:1',
#                         'flavor_name:m1.tiny',
#                     ],
#                 )
#             elif is_mandatory(value):
#                 not_found_metrics.append(key)
#     assert not_found_metrics == [], f"No nova flavor metrics found: {not_found_metrics}"
#
#
# def test_hypervisor_service_check_up(aggregator, dd_run_check, instance, monkeypatch):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     tags = [
#         'domain_id:default',
#         'keystone_server:{}'.format(instance["keystone_server_url"]),
#         'aggregate:my-aggregate',
#         'availability_zone:availability-zone',
#         'hypervisor:agent-integrations-openstack-default',
#         'hypervisor_id:1',
#         'status:enabled',
#         'virt_type:QEMU',
#     ]
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#     aggregator.assert_service_check('openstack.nova.hypervisor.up', status=AgentCheck.OK, tags=tags)
#
#
# def test_hypervisor_service_check_down(aggregator, dd_run_check, instance, monkeypatch):
#     http = MockHttp(
#         "agent-integrations-openstack-default",
#         replace={
#             'compute/v2.1/os-hypervisors/detail?with_servers=true': lambda d: {
#                 **d,
#                 **{
#                     'hypervisors': d['hypervisors'][:0]
#                     + [{**d['hypervisors'][0], **{'state': 'down'}}]
#                     + d['hypervisors'][1:]
#                 },
#             }
#         },
#     )
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     tags = [
#         'domain_id:default',
#         'keystone_server:{}'.format(instance["keystone_server_url"]),
#         'aggregate:my-aggregate',
#         'availability_zone:availability-zone',
#         'hypervisor:agent-integrations-openstack-default',
#         'hypervisor_id:1',
#         'status:enabled',
#         'virt_type:QEMU',
#     ]
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#     aggregator.assert_service_check('openstack.nova.hypervisor.up', status=AgentCheck.CRITICAL, tags=tags)
#
#
# @pytest.mark.parametrize(
#     "instance, hypervisor_id",
#     [
#         pytest.param(CONFIG, '1', id="default"),
#         pytest.param(CONFIG_NOVA_MICROVERSION_LATEST, 'd884b51a-e464-49dc-916c-766da0237661', id="latest"),
#     ],
# )
# def test_hypervisor_metrics(aggregator, dd_run_check, instance, hypervisor_id, monkeypatch):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#     not_found_metrics = []
#     for key, value in NOVA_HYPERVISOR_METRICS.items():
#         if check_microversion(instance, value):
#             if key in aggregator.metric_names:
#                 aggregator.assert_metric(
#                     key,
#                     tags=[
#                         'domain_id:default',
#                         'keystone_server:{}'.format(instance["keystone_server_url"]),
#                         'aggregate:my-aggregate',
#                         'availability_zone:availability-zone',
#                         'hypervisor:agent-integrations-openstack-default',
#                         'hypervisor_id:{}'.format(hypervisor_id),
#                         'status:enabled',
#                         'virt_type:QEMU',
#                     ],
#                 )
#             elif is_mandatory(value):
#                 not_found_metrics.append(key)
#     assert not_found_metrics == [], f"No nova hypervisor metrics found: {not_found_metrics}"
#
#
# def test_nova_metrics_ironic(aggregator, caplog, dd_run_check, instance_ironic_nova_microversion_latest, monkeypatch):
#     http = MockHttp("agent-integrations-openstack-ironic")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     caplog.set_level(logging.DEBUG)
#     check = OpenStackControllerCheck('test', {}, [instance_ironic_nova_microversion_latest])
#     dd_run_check(check)
#
#     found = False
#     for metric in aggregator.metric_names:
#         if metric in NOVA_QUOTA_SETS_METRICS:
#             found = True
#
#     assert found, "No quota metrics found"
#
#     found = False
#     for metric in aggregator.metric_names:
#         if metric in NOVA_LIMITS_METRICS:
#             found = True
#
#     assert found, "No quota metrics found"
#
#     found = False
#     for metric in aggregator.metric_names:
#         if metric in NOVA_FLAVOR_METRICS:
#             found = True
#     assert found, "No flavor metrics found"
#
#     for metric in aggregator.metric_names:
#         if metric in NOVA_HYPERVISOR_METRICS:
#             found = True
#     assert found, "No flavor metrics found"
#
#     aggregator.assert_metric('openstack.nova.hypervisor.load_15', count=0)
#     assert "Skipping uptime metrics for bare metal hypervisor 9d72cf53-19c8-4942-9314-005fa5d2a6a0" in caplog.text
#
#
# def test_latest_service_metrics(aggregator, dd_run_check, instance_nova_microversion_latest, monkeypatch):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance_nova_microversion_latest])
#     dd_run_check(check)
#
#     tags = [
#         'domain_id:default',
#         'keystone_server:{}'.format(instance_nova_microversion_latest["keystone_server_url"]),
#     ]
#
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_compute',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:7bf08d7e-a939-46c3-bdae-fbe3ebfe78a4',
#             'service_status:enabled',
#             'availability_zone:availability-zone',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_conductor',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:df55f706-a60e-4d3d-8cd6-30f5b33d79ce',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_conductor',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:aadbda65-f523-419a-b3df-c287d196a2c1',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_scheduler',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:2ec2027d-ac70-4e2b-95ed-fb1756d24996',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#
#
# def test_default_service_metrics(aggregator, dd_run_check, instance, monkeypatch):
#     http = MockHttp("agent-integrations-openstack-default")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#
#     tags = ['domain_id:default', 'keystone_server:{}'.format(instance["keystone_server_url"])]
#
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_compute',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:3',
#             'service_status:enabled',
#             'availability_zone:availability-zone',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_conductor',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:5',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_conductor',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:1',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_scheduler',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-default',
#             'service_id:2',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#
#
# def test_default_ironic_service_metrics(aggregator, dd_run_check, instance, monkeypatch):
#     http = MockHttp("agent-integrations-openstack-ironic")
#     monkeypatch.setattr('requests.get', mock.MagicMock(side_effect=http.get))
#     monkeypatch.setattr('requests.post', mock.MagicMock(side_effect=http.post))
#
#     check = OpenStackControllerCheck('test', {}, [instance])
#     dd_run_check(check)
#
#     tags = ['domain_id:default', 'keystone_server:{}'.format(instance["keystone_server_url"])]
#
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_compute',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-ironic',
#             'service_id:3',
#             'service_status:enabled',
#             'availability_zone:nova',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_conductor',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-ironic',
#             'service_id:5',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_conductor',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-ironic',
#             'service_id:1',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
#     aggregator.assert_metric(
#         "openstack.nova.service.up",
#         count=1,
#         value=1,
#         tags=tags
#         + [
#             'service_name:nova_scheduler',
#             'service_state:up',
#             'service_host:agent-integrations-openstack-ironic',
#             'service_id:2',
#             'service_status:enabled',
#             'availability_zone:internal',
#         ],
#     )
