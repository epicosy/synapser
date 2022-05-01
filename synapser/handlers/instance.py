from threading import Thread
from typing import Dict, Any

from cement import Handler

from synapser.core.data.api import RepairRequest, CoverageRequest
from synapser.core.database import Instance
from synapser.core.interfaces import HandlersInterface


class InstanceHandler(HandlersInterface, Handler):
    class Meta:
        label = 'instance'

    def dispatch(self, signals: Dict[str, Any], repair_request: RepairRequest) -> int:
        tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)
        signal_handler = self.app.handler.get('handlers', 'signal', setup=True)
        signal_cmds = signal_handler.get_commands(signals)
        file, locs = next(iter( repair_request.manifest.items() ))
        rid = self.app.db.add(Instance(status='running', name=self.app.plugin.tool, target=file, iid=repair_request.iid,
                                       path=str(repair_request.working_dir)))

        repair_cmd = tool_handler.repair(signals=signal_cmds, repair_request=repair_request)
        repair_thread = Thread(target=tool_handler.dispatch, args=(rid, repair_cmd, repair_request))
        repair_thread.setDaemon(True)
        repair_thread.start()

        return rid

    def coverage(self, signals: Dict[str, Any], coverage_request: CoverageRequest) -> int:
        tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)
        signal_handler = self.app.handler.get('handlers', 'signal', setup=True)
        signal_cmds = signal_handler.get_commands(signals)
        cid = self.app.db.add(Instance(status='running', name=self.app.plugin.tool, target=coverage_request.manifest[0],
                                       path=str(coverage_request.working_dir), iid=coverage_request.iid))
        tool_handler.coverage(signals=signal_cmds, coverage_request=coverage_request)
        self.app.db.update(Instance, cid, 'status', 'done')
        self.app.log.info(f"Coverage instance {cid} finished execution.")

        return cid

    def get(self, rid: int):
        return self.app.db.query(Instance, rid)
