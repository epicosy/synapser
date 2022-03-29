import json
import base64
from typing import Tuple, List

import requests
from cement import Handler
from requests import Response

from synapser.core.database import Signal
from synapser.core.exc import SynapserError, CommandError
from synapser.core.interfaces import HandlersInterface


def check_response(response: Response):
    try:
        response_json = response.json()
        response_error = None

        if not response_json:
            raise SynapserError(f'API request to {response.url} returned empty response.')

        if isinstance(response_json, list):
            for r in response_json:
                if isinstance(r, dict):
                    response_error = r.get('error', None)
                    if response_error:
                        break

        if response_error:
            raise SynapserError(f"API request to {response.url} failed. {response_error}")

        return response_json

    except json.decoder.JSONDecodeError:
        pass

    if response.status_code != 200:
        raise SynapserError(f'API request to {response.url} failed. {response.reason}')

    return response


class SignalHandler(HandlersInterface, Handler):
    class Meta:
        label = 'signal'

    def get_commands(self, signals: dict) -> dict:
        singal_cmds = {}

        for arg, signal in signals.items():
            sid, placeholders = self.save(arg=arg, url=signal['url'], data=signal['data'],
                                          placeholders=signal['placeholders'])
            if placeholders:
                singal_cmds[arg] = f"synapser signal --id {sid} --placeholders {placeholders}"
            else:
                singal_cmds[arg] = f"synapser signal --id {sid}"

        return singal_cmds

    def save(self, arg: str, url: str, data: dict, placeholders: dict) -> Tuple[int, str]:
        placeholders_wrapper = {}
        placeholders_arg = ""
        self.app.log.info(f"DATA: {data}")
        for i, (k, v) in enumerate(placeholders.items(), 1):
            placeholders_wrapper[f"p{i}"] = k
            placeholders_arg += f" p{i}:{v}"

        encoded_data = base64.b64encode(json.dumps(data).encode()).decode()
        encoded_placeholders = base64.b64encode(json.dumps(placeholders_wrapper).encode()).decode()

        return self.app.db.add(
            Signal(arg=arg, url=url, data=encoded_data, placeholders=encoded_placeholders)), placeholders_arg

    def load(self, sid: int) -> Signal:
        return self.app.db.query(Signal, sid)

    def parse(self, sid: int, placeholders_wrapper: List[str], extra_args: List[str] = None) -> Tuple[Signal, dict, dict]:
        signal = self.load(sid)
        data, placeholders = signal.decoded()

        if placeholders_wrapper:
            # get filled placeholders
            parsed_extra_args = {}

            if extra_args:
                try:
                    tool_handler = self.app.handler.get('handlers', self.app.plugin.tool, setup=True)
                    # parse extra arguments added by the tool
                    parsed_extra_args = tool_handler.parse_extra(extra_args=extra_args, signal=signal)
                except (ValueError, CommandError) as e:
                    self.app.log.error(e)

            for p in placeholders_wrapper:
                # match with original arguments
                try:
                    k, v = p.split(':')

                    if v in parsed_extra_args:
                        data['args'][placeholders[k]] = parsed_extra_args[v]
                    elif k in placeholders:
                        data['args'][placeholders[k]] = v

                except (ValueError, CommandError) as e:
                    self.app.log.error(e)
                    continue

        return signal, data, placeholders


class APIHandler(HandlersInterface, Handler):
    class Meta:
        label = 'api'

    def __call__(self, url: str, json_data: dict, *args, **kwargs) -> dict:
        self.app.log.debug(f"POST {url}: {json_data}")
        response = requests.post(url, json=json_data)
        return check_response(response)


class BuildAPIHandler(APIHandler):
    class Meta:
        label = 'build_api'

    def __call__(self, signal: Signal, data: dict, *args, **kwargs) -> bool:
        response_json = super().__call__(signal.url, data)

        if isinstance(response_json, list):
            for r in response_json:
                exit_status = int(r.get('exit_status', 255))

                if exit_status != 0:
                    return False

            return True
        else:
            exit_status = int(response_json.get('exit_status', 255))

        return exit_status == 0


class TestAPIHandler(APIHandler):
    class Meta:
        label = 'test_api'

    def __call__(self, signal: Signal, data: dict, *args, **kwargs) -> bool:
        response_json = super().__call__(signal.url, data)

        if isinstance(response_json, list):
            for r in response_json:
                exit_status = int(r.get('exit_status', 255))
                passed = r.get('passed', False)

                if exit_status != 0:
                    return False

                if not passed:
                    return False

            return True
        else:
            exit_status = int(response_json.get('exit_status', 255))
            passed = response_json.get('passed', False)

        if not passed:
            return False

        return exit_status == 0
