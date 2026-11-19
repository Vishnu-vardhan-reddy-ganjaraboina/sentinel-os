import sys

import pytest

from sentinel.execution.isolated_worker import IsolatedWorker


@pytest.mark.skipif(sys.platform != "linux", reason="Linux-only bubblewrap profile")
def test_bubblewrap_profile_fails_closed_when_dependency_missing(tmp_path, monkeypatch):
    import sentinel.execution.isolated_worker as module
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="required for OS sandboxing"):
        IsolatedWorker(allowed_modules={"tests"}, cwd=tmp_path, bubblewrap=True)
