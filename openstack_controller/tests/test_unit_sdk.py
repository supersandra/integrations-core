# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import pytest

from datadog_checks.openstack_controller import OpenStackControllerCheck

from .common import TEST_OPENSTACK_NO_AUTH_CONFIG_PATH

pytestmark = [pytest.mark.unit]


def test_sdk_exception(aggregator, dd_run_check, instance_sdk, caplog, monkeypatch):
    instance_sdk['openstack_config_file_path'] = TEST_OPENSTACK_NO_AUTH_CONFIG_PATH
    print(instance_sdk['openstack_config_file_path'])
    check = OpenStackControllerCheck('test', {}, [instance_sdk])
    dd_run_check(check)
    assert False
