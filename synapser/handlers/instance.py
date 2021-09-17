from threading import Thread
from typing import Dict, Any

from cement import Handler

from synapser.core.database import Instance
from synapser.core.interfaces import HandlersInterface


class InstanceHandler(HandlersInterface, Handler):
    class Meta:
        label = 'instance'

    def dispatch(self, signals: Dict[str, Any], timeout: str, working_dir: str, target: str, **kwargs) -> int:
        tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)
        signal_handler = self.app.handler.get('handlers', 'signal', setup=True)
        singal_cmds = {}

        for arg, signal in signals.items():
            sid, placeholders = signal_handler.save(url=signal['url'], data=signal['data'],
                                                    placeholders=signal['placeholders'])
            if placeholders:
                singal_cmds[arg] = f"synapser signal --id {sid} --placeholders {placeholders}"
            else:
                singal_cmds[arg] = f"synapser signal --id {sid}"

        rid = self.app.db.add(Instance(status='running', name=self.app.plugin.tool, path=working_dir, target=target))

        # with daemon.DaemonContext(detach_process=True) as rd:
        #    self.app.log.warning(rd.gid)
        ws_data = tool_handler.repair(signals=singal_cmds, timeout=int(timeout), working_dir=working_dir, target=target,
                                      **kwargs)

        repair_thread = Thread(target=tool_handler.dispatch, args=(rid, ws_data))
        repair_thread.setDaemon(True)
        repair_thread.start()

        return rid

    def get(self, rid: int):
        return self.app.db.query(Instance, rid)
