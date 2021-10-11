from abc import abstractmethod
from pathlib import Path
from typing import Union

from synapser.core.data.api import RepairRequest
from synapser.core.data.configs import ToolConfigs
from synapser.core.data.results import CommandData, Patch, WebSocketData, RepairCommand
from synapser.core.database import Instance
from synapser.core.websockets import WebSocketProcessFactory
from synapser.handlers.command import CommandHandler


class ToolHandler(CommandHandler):
    class Meta:
        label = 'tool'

    def get_config(self, key: str):
        return self.app.config.get(self.Meta.label, key)

    def get_configs(self):
        configs = self.app.config.get_section_dict(self.Meta.label).copy()

        return ToolConfigs(name=self.Meta.label, **configs)

    @abstractmethod
    def repair(self, signals: dict, repair_request: RepairRequest) -> RepairCommand:
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

    def dispatch(self, rid: int, repair_cmd: RepairCommand, repair_request: RepairRequest):
        ws_data = WebSocketData(path=repair_cmd.configs.full_path, args=repair_cmd.to_list(),
                                cwd=str(repair_request.working_dir),  timeout=repair_request.timeout)
        factory = WebSocketProcessFactory(ws_data=ws_data, finish=self.finish, rid=rid, logger=self.app.log)
        self.app.db.update(Instance, rid, 'socket', factory.listener.getHost().port)
        factory.run()
