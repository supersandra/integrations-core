# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import pytest
import platform
from datadog_checks.scylla import ScyllaCheck

from .common import INSTANCE_DEFAULT_METRICS, INSTANCE_DEFAULT_METRICS_V2



@pytest.mark.e2e
def test_check_ok(dd_agent_check):
    aggregator = dd_agent_check(rate=True)

    for metric in INSTANCE_DEFAULT_METRICS:
        aggregator.assert_metric(metric)
    aggregator.assert_all_metrics_covered()

    aggregator.assert_service_check('scylla.prometheus.health', ScyllaCheck.OK)


@pytest.mark.skipif(platform.python_version() < "3", reason='OpenMetrics V2 is only available with Python 3')
@pytest.mark.e2e
def test_check_ok_omv2(dd_agent_check, dd_environment_omv2):
    aggregator = dd_agent_check(omv2_instance, rate=True)
    for metric in INSTANCE_DEFAULT_METRICS_V2:
        aggregator.assert_metric(metric)

    aggregator.assert_all_metrics_covered()
    aggregator.assert_service_check('scylla.openmetrics.health', ScyllaCheck.OK)