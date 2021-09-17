from abc import abstractmethod
from pathlib import Path
from typing import Union

from synapser.core.data.configs import ToolConfigs
from synapser.core.data.results import CommandData, Patch, WebSocketData
from synapser.core.database import Instance
from synapser.core.websockets import WebSocketProcessFactory
from synapser.handlers.command import CommandHandler


class ToolHandler(CommandHandler):
    class Meta:
        label = 'tool'

    def get_config(self, key: str):
        return self.app.config.get(self.Meta.label, key)

    def get_configs(self, args: dict = None):
        configs = self.app.config.get_section_dict(self.Meta.label).copy()

        if args:
            if 'args' in configs:
                configs['args'].update(args)
            else:
                configs['args'] = args

        return ToolConfigs(name=self.Meta.label, **configs)

    @abstractmethod
    def repair(self, signals: dict, timeout: int, working_dir: str, target: str, **kwargs) -> int:
        pass

    @abstractmethod
    def help(self) -> CommandData:
        pass

    def get_diff(self, original: Path, patch: Path) -> str:
        self.log = False
        diff_data = super().__call__(CommandData(args=f"diff {original} {patch}"))

        return diff_data.output

    def get_patch(self, original: Path, patch: Path, is_fix: bool = False) -> Union[Patch, None]:
        return Patch(is_fix=is_fix, patch_file=patch, source_file=original, change=self.get_diff(original, patch))

    def finish(self, rid: int):
        self.app.db.update(Instance, rid, 'socket', None)
        self.app.db.update(Instance, rid, 'status', 'done')
        self.app.log.info(f"Repair instance {rid} finished execution.")

    def dispatch(self, rid: int, ws_data: WebSocketData):
        factory = WebSocketProcessFactory(ws_data=ws_data, finish=self.finish, rid=rid, logger=self.app.log)
        self.app.db.update(Instance, rid, 'socket', factory.listener.getHost().port)
        factory.run()
