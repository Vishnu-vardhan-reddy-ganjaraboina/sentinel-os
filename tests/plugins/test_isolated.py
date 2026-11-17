from sentinel.execution.isolated_worker import IsolatedWorker
from sentinel.plugins.constants import PluginState
from sentinel.plugins.isolated import IsolatedPlugin


def test_isolated_plugin_lifecycle_hooks_run_in_worker():
    plugin = IsolatedPlugin(
        "isolated-test",
        worker=IsolatedWorker(
            allowed_modules={"tests.execution.worker_fixtures"},
        ),
        hooks={
            "load": "tests.execution.worker_fixtures:plugin_hook",
        },
    )
    plugin.load()
    assert plugin.state is PluginState.LOADED
    plugin.enable()
    assert plugin.state is PluginState.ENABLED
    plugin.disable()
    plugin.unload()
    assert plugin.state is PluginState.UNLOADED
