# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import logging

import pytest

from datadog_checks.dev.http import MockResponse
from datadog_checks.openstack_controller import OpenStackControllerCheck

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'exceptions': {'identity/v3/auth/tokens': Exception()},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_auth_exception(aggregator, dd_run_check, instance, caplog, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    assert 'Exception while authorizing user' in caplog.text


@pytest.mark.parametrize(
    'mock_api_rest',
    [
        pytest.param(
            {
                'host': 'agent-integrations-openstack-default',
                'defaults': {'identity/v3/auth/tokens': MockResponse(status_code=401)},
            },
            id='',
        )
    ],
    indirect=['mock_api_rest'],
)
def test_auth_http_error(aggregator, dd_run_check, instance, caplog, mock_api_rest):
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    assert 'Exception while authorizing user' in caplog.text


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
def test_auth_ok(aggregator, dd_run_check, instance, caplog, mock_api_rest):
    caplog.set_level(logging.INFO)
    check = OpenStackControllerCheck('test', {}, [instance])
    dd_run_check(check)
    assert 'User successfully authorized' in caplog.text
