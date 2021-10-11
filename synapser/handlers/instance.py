from threading import Thread
from typing import Dict, Any

from cement import Handler

from synapser.core.data.api import RepairRequest
from synapser.core.database import Instance
from synapser.core.interfaces import HandlersInterface


class InstanceHandler(HandlersInterface, Handler):
    class Meta:
        label = 'instance'

    def dispatch(self, signals: Dict[str, Any], repair_request: RepairRequest) -> int:
        tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)
        signal_handler = self.app.handler.get('handlers', 'signal', setup=True)
        signal_cmds = signal_handler.get_commands(signals)
        rid = self.app.db.add(Instance(status='running', name=self.app.plugin.tool, path=repair_request.working_dir,
                                       target=repair_request.manifest[0]))

        repair_cmd = tool_handler.repair(signals=signal_cmds, repair_request=repair_request)
        repair_thread = Thread(target=tool_handler.dispatch, args=(rid, repair_cmd, repair_request))
        repair_thread.setDaemon(True)
        repair_thread.start()

        return rid

    def get(self, rid: int):
        return self.app.db.query(Instance, rid)
