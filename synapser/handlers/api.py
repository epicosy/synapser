import json
import base64
from typing import Tuple, List

import requests
from cement import Handler
from requests import Response

from synapser.core.database import Signal
from synapser.core.exc import SynapserError
from synapser.core.interfaces import HandlersInterface


def check_response(response: Response):
    try:
        response_json = response.json()

        if not response_json:
            raise SynapserError(f'API request to {response.url} returned empty response.')

        response_error = response_json.get('error', None)

        if response_error:
            raise SynapserError(f"API request to {response.url} failed. {response_error}")

    except json.decoder.JSONDecodeError:
        pass

    if response.status_code != 200:
        raise SynapserError(f'API request to {response.url} failed. {response.reason}')

    return response


class SignalHandler(HandlersInterface, Handler):
    class Meta:
        label = 'signal'

    def save(self, url: str, data: dict, placeholders: dict) -> Tuple[int, str]:
        placeholders_wrapper = {}
        placeholders_arg = ""

        for i, (k, v) in enumerate(placeholders.items(), 1):
            placeholders_wrapper[f"p{i}"] = k
            placeholders_arg += f" p{i}:{v}"

        encoded_data = base64.b64encode(json.dumps(data).encode()).decode()
        encoded_placeholders = base64.b64encode(json.dumps(placeholders_wrapper).encode()).decode()

        return self.app.db.add(Signal(url=url, data=encoded_data, placeholders=encoded_placeholders)), placeholders_arg

    def load(self, sid: int) -> Signal:
        return self.app.db.query(Signal, sid)

    def transmit(self, sid: int, placeholders_wrapper: List[str]) -> bool:
        signal = self.load(sid)
        data, placeholders = signal.decoded()

        if placeholders_wrapper:
            # get filled placeholders
            for p in placeholders_wrapper:
                # match with original arguments
                k, v = p.split(':')
                data['args'][placeholders[k]] = v

        try:
            response = requests.post(signal.url, json=data)
            check_response(response)
            return int(response.json()['return_code']) == 0
        except SynapserError as se:
            self.app.log.error(str(se))
            return False
