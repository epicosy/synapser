from typing import Tuple

from cement import Handler

from synapser.core.data.results import CommandData
from synapser.core.database import Instance
from synapser.core.interfaces import HandlersInterface


class InstanceHandler(HandlersInterface, Handler):
    class Meta:
        label = 'instance'

    def dispatch(self, benchmark_endpoint: str, test_command: str, compiler_command: str, timeout: str,
                 **kwargs) -> Tuple[int, CommandData]:
        tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)

        cmd_data = tool_handler.repair(test_command=f"\'synapser test -e {benchmark_endpoint} -c {test_command}\'",
                                       compiler_command=f"\'synapser compile -e {benchmark_endpoint} -c {compiler_command}\'",
                                       timeout=int(timeout), **kwargs)
        return self.add(cmd_data.pid), cmd_data

    def add(self, pid: int, status: str = 'running'):
        return self.app.db.add(Instance(pid=pid, status=status, name='genprog'))
