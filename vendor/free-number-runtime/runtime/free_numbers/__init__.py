"""Demand runtime v0.1.1 over Free Numbers Core v1.0.0.

Compression does not define identity. No operation deletes a retained scalar.
"""
from .algebra import Q, ZERO, ONE, BASIS
from .retention import Vault, Meter
from .expression import (Tensor, Circuit, Channel, Observation, block, matrix_block,
                         retained, compression, read, constant, component)
from .demand import Scope, Query, Policy, Plan, plan, verify_plan
from .evaluate import (Certificate, evaluate, verify_certificate, replacement_query,
                       assess_replacement, ReplacementJudgement)
