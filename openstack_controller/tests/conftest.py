# (C) Datadog, Inc. 2019-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import json
import os
import re
import tempfile
from copy import deepcopy

import mock
import pytest
from mock import MagicMock

from datadog_checks.dev import docker_run
from datadog_checks.dev.conditions import CheckDockerLogs
from datadog_checks.dev.fs import get_here
from datadog_checks.dev.http import MockResponse
from datadog_checks.openstack_controller import OpenStackControllerCheck

from .common import (
    CHECK_NAME,
    CONFIG,
    CONFIG_NOVA_IRONIC_MICROVERSION_LATEST,
    CONFIG_NOVA_MICROVERSION_LATEST,
    CONFIG_SDK,
    TEST_OPENSTACK_CONFIG_PATH,
    USE_OPENSTACK_SANDBOX,
    MockHttp,
)
from .ssh_tunnel import socks_proxy
from .terraform import terraform_run


def mock_endpoint_response_time(endpoint):
    mock_total_seconds = mock.MagicMock(return_value=3)
    mock_elapsed = mock.MagicMock()
    mock_elapsed.total_seconds = mock_total_seconds
    mock_endpoint = MockResponse(
        file_path=os.path.join(get_here(), endpoint),
        status_code=200,
    )
    mock_endpoint.elapsed = mock_elapsed
    return mock_endpoint


@pytest.fixture(scope='session')
def dd_environment():
    if USE_OPENSTACK_SANDBOX:
        with terraform_run(os.path.join(get_here(), 'terraform')) as outputs:
            ip = outputs['ip']['value']
            internal_ip = outputs['internal_ip']['value']
            private_key = outputs['ssh_private_key']['value']
            instance = {
                'keystone_server_url': 'http://{}/identity'.format(internal_ip),
                'username': 'admin',
                'password': 'password',
                'ssl_verify': False,
                'nova_microversion': '2.93',
                'ironic_microversion': '1.80',
                # 'openstack_cloud_name': 'test_cloud',
                # 'openstack_config_file_path': '/tmp/openstack_config.yaml',
            }
            config_file = os.path.join(tempfile.gettempdir(), 'openstack_controller_instance.json')
            with open(config_file, 'wb') as f:
                output = json.dumps(instance).encode('utf-8')
                f.write(output)
            env = dict(os.environ)
            with socks_proxy(
                ip,
                re.sub('([.@])', '_', env['TF_VAR_user']).lower(),
                private_key,
            ) as socks:
                print("socks: %s", socks)
                socks_ip, socks_port = socks
                # agent_config = {
                #     'proxy': {'http': 'socks5://{}:{}'.format(socks_ip, socks_port)},
                # }
                agent_config = {
                    'proxy': {'http': 'socks5://{}:{}'.format(socks_ip, socks_port)},
                    'docker_volumes': ['{}:/tmp/openstack_config.yaml'.format(TEST_OPENSTACK_CONFIG_PATH)],
                }
                yield instance, agent_config
    else:
        compose_file = os.path.join(get_here(), 'docker', 'docker-compose.yaml')
        conditions = [
            CheckDockerLogs(identifier='openstack-keystone', patterns=['server running']),
            CheckDockerLogs(identifier='openstack-nova', patterns=['server running']),
            CheckDockerLogs(identifier='openstack-neutron', patterns=['server running']),
            CheckDockerLogs(identifier='openstack-ironic', patterns=['server running']),
        ]
        with docker_run(compose_file, conditions=conditions):
            instance = {
                'keystone_server_url': 'http://127.0.0.1:8080/identity',
                'username': 'admin',
                'password': 'password',
                'ssl_verify': False,
            }
            yield instance


@pytest.fixture
def instance():
    return deepcopy(CONFIG)


@pytest.fixture
def instance_nova_microversion_latest():
    return deepcopy(CONFIG_NOVA_MICROVERSION_LATEST)


@pytest.fixture
def instance_ironic_nova_microversion_latest():
    return deepcopy(CONFIG_NOVA_IRONIC_MICROVERSION_LATEST)


@pytest.fixture
def instance_sdk():
    return deepcopy(CONFIG_SDK)


@pytest.fixture
def check(instance):
    return OpenStackControllerCheck(CHECK_NAME, {}, [instance])


@pytest.fixture
def mock_api_rest(request, monkeypatch):
    api_rest = MockHttp(**request.param)
    mock_api_rest = MagicMock()
    mock_api_rest.get = MagicMock(side_effect=api_rest.get)
    mock_api_rest.post = MagicMock(side_effect=api_rest.post)
    monkeypatch.setattr('requests.get', mock_api_rest.get)
    monkeypatch.setattr('requests.post', mock_api_rest.post)
    yield mock_api_rest


@pytest.fixture
def mock_http_post(request, monkeypatch):
    mock_post = MagicMock(side_effect=MockHttp(**request.param).post)
    monkeypatch.setattr('requests.post', mock_post)
    yield mock_post
