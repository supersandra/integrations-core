# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)

try:
    import tagger
except ImportError:
    from ..stubs import tagger
