
from typing import Dict, Any

from cement import Handler

from synapser.core.interfaces import HandlersInterface


class InstanceHandler(HandlersInterface, Handler):
    class Meta:
        label = 'instance'

    def dispatch(self, signals: Dict[str, Any], timeout: str, working_dir: str, **kwargs) -> int:
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

        #with daemon.DaemonContext(detach_process=True) as rd:
        #    self.app.log.warning(rd.gid)
        return tool_handler.repair(signals=singal_cmds, timeout=int(timeout), working_dir=working_dir, **kwargs)
