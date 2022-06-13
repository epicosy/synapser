from abc import abstractmethod
from pathlib import Path
from typing import Union, List
from sqlalchemy.sql import func

from synapser.core.data.api import RepairRequest
from synapser.core.data.results import CommandData, Patch, WebSocketData, RepairCommand
from synapser.core.data.schema import parse_configs
from synapser.core.database import Instance, Signal
from synapser.core.websockets import WebSocketProcessFactory
from synapser.handlers.api import BuildAPIHandler, TestAPIHandler, APIHandler, TestBatchAPIHandler
from synapser.handlers.command import CommandHandler


class ToolHandler(CommandHandler):
    """
        Handler for tools.
    """
    class Meta:
        label = 'tool'
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self._repair_cmd = None
        self._configs = None
        self._api_handlers = {
            'build': BuildAPIHandler,
            'test': TestAPIHandler,
            'testbatch': TestBatchAPIHandler
        }

    def register(self, cmd: str) -> APIHandler:
        """
            Registers and inits API handler

            :param str cmd: name of the arg the tool calls as command
            :return: instantiated handler
        """
        configs = self.get_configs()
        api_cmd = configs.api_cmds[cmd]
        api_handler = self._api_handlers[api_cmd]
        self.app.handler.register(api_handler)

        return self.app.handler.get('handlers', api_handler.Meta.label, setup=True)

    def get_configs(self):
        """
            Parses and returns the tool's configs.
        """
        configs = self.app.config.get_section_dict(self.Meta.label).copy()

        return parse_configs(self.Meta.label, configs)

    @property
    def repair_cmd(self):
        """
            Returns the repair command for the tool.
        """
        if not self._repair_cmd:
            self._repair_cmd = RepairCommand(configs=self.configs)

        return self._repair_cmd

    @property
    def configs(self):
        """
            Returns the repair tool's configs.
        """
        if not self._configs:
            self._configs = self.get_configs()

        return self._configs

    @abstractmethod
    def repair(self, signals: dict, repair_request: RepairRequest) -> RepairCommand:
        pass
    
    def help(self) -> CommandData:
        """
            Returns the help message of the repair tool.
        """
        configs = self.get_configs()
    
        if configs.help:    
            return super().__call__(cmd_data=CommandData(path=configs.full_path, args=configs.help_cmd))
        
        return CommandData(path=configs.full_path, args="", 
                           output=f"'help' flag not configured in {configs.name} tool's configs.")
        
    @abstractmethod
    def parse_extra(self, extra_args: List[str], signal: Signal) -> str:
        """
            Parses extra arguments in the signals.
        """
        pass

    def get_diff(self, original: Path, patch: Path) -> str:
        """
            Diff between original file and patch file.
        """
        self.log = False
        diff_data = super().__call__(CommandData(args=f"diff {original} {patch}"))

        return diff_data.output

    def get_patch(self, original: Path, patch: Path, is_fix: bool = False) -> Patch:
        """
            Instantiates the patch file into the Patch object data class.
        """
        return Patch(is_fix=is_fix, patch_file=patch, source_file=original, change=self.get_diff(original, patch))

    def finish(self, rid: int):
        """
            Notifies the socket connection to end and updates the database with the repair instance status.
        """
        self.app.db.update(Instance, rid, 'socket', None)
        self.app.db.update(Instance, rid, 'status', 'done')
        self.app.db.update(Instance, rid, 'end', func.now())
        self.app.log.info(f"Repair instance {rid} finished execution.")

    def dispatch(self, rid: int, repair_cmd: RepairCommand, repair_request: RepairRequest):
        """
            Dispatches the repair request to be run as a ProcessCommand.
        """
        ws_data = WebSocketData(path=repair_cmd.configs.full_path, args=repair_cmd.to_list(),
                                cwd=repair_cmd.cwd if repair_cmd.cwd else str(repair_request.working_dir),
                                timeout=repair_request.timeout)
        factory = WebSocketProcessFactory(ws_data=ws_data, finish=self.finish, rid=rid, logger=self.app.log)
        self.app.db.update(Instance, rid, 'socket', factory.listener.getHost().port)
        factory.run()
