import os
import tempfile
from unittest.mock import patch

from family_backend.control import CURRENT_CONTEXT, OperationContext


def isolate_controls(test):
    directory = tempfile.TemporaryDirectory()
    test.addCleanup(directory.cleanup)
    environment = patch.dict(os.environ, {"FAMILY_CONTROL_DB": directory.name + "/control.sqlite3"})
    environment.start()
    test.addCleanup(environment.stop)
    token = CURRENT_CONTEXT.set(OperationContext("local-test-user", "local-test-chat", "local-test-turn"))
    test.addCleanup(CURRENT_CONTEXT.reset, token)
