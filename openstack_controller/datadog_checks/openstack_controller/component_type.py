# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

from enum import Enum


class ComponentType(str, Enum):
    IDENTITY = 'identity'
    COMPUTE = 'compute'
    NETWORK = 'network'
    BLOCK_STORAGE = 'block-storage'
    BAREMETAL = 'baremetal'
    LOAD_BALANCER = 'load-balancer'
