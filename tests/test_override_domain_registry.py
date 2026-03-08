import unittest

import semantic_overrides
from lcmodel.overrides import CORE_COMPAT_OVERRIDES, POSTSCRIPT_OVERRIDES, WORKFLOW_OVERRIDES


class TestOverrideDomainRegistry(unittest.TestCase):
    def test_domain_registries_do_not_overlap(self):
        workflow = set(WORKFLOW_OVERRIDES)
        core = set(CORE_COMPAT_OVERRIDES)
        postscript = set(POSTSCRIPT_OVERRIDES)
        self.assertEqual(set(), workflow & core)
        self.assertEqual(set(), workflow & postscript)
        self.assertEqual(set(), core & postscript)

    def test_semantic_registry_is_domain_composition(self):
        composed = {}
        composed.update(WORKFLOW_OVERRIDES)
        composed.update(CORE_COMPAT_OVERRIDES)
        composed.update(POSTSCRIPT_OVERRIDES)
        self.assertEqual(composed, semantic_overrides.SEMANTIC_OVERRIDES)
        self.assertEqual(149, len(semantic_overrides.SEMANTIC_OVERRIDES))

