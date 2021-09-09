from typing import Tuple

from cement import Handler

from synapser.core.data.results import CommandData
from synapser.core.database import Instance
from synapser.core.interfaces import HandlersInterface


class InstanceHandler(HandlersInterface, Handler):
    class Meta:
        label = 'instance'

    def dispatch(self, test_signal: dict, compiler_signal: dict, timeout: str,
                 **kwargs) -> Tuple[int, CommandData]:
        tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)
        signal_handler = self.app.handler.get('handlers', 'signal', setup=True)

        tsid = signal_handler.save(url=test_signal['url'], data=test_signal['json'])
        csid = signal_handler.save(url=compiler_signal['url'], data=compiler_signal['json'])

        cmd_data = tool_handler.repair(test_command=f"\'synapser signal --id {tsid}\'",
                                       compiler_command=f"\'synapser signal --id {csid}\'",
                                       timeout=int(timeout), **kwargs)

        return self.add(cmd_data.pid, test_sid=tsid, compile_sid=csid), cmd_data

    def add(self, pid: int, test_sid: int, compile_sid: int, status: str = 'running'):
        return self.app.db.add(Instance(pid=pid, status=status, name='genprog', tsid=test_sid, csid=compile_sid))
