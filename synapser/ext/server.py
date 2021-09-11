from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from synapser.controllers.base import VERSION_BANNER
from synapser.core.exc import SynapserError, BadRequestError
from typing import List


def verify_bad_request(data, keys: List[str], format_error: str):
    for key in keys:
        if not data.get(key, None):
            raise BadRequestError(format_error.format(key))


def setup_api(app):
    api = Flask('synapser')
    api.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    api.config["SQLALCHEMY_DATABASE_URI"] = app.db.engine.url
    ma = Marshmallow(api)

    @api.route('/', methods=['GET'])
    def index():
        tool = app.handler.get('handlers', app.plugin.tool, setup=True)
        return f"{VERSION_BANNER}\nServing {app.plugin.tool}\n{tool.help().output}"

    @api.route('/repair', methods=['POST'])
    def repair():
        if request.is_json:
            data = request.get_json()

            try:
                verify_bad_request(data, keys=['signals', 'timeout', 'args'],
                                   format_error="This request was not properly formatted, must specify '{}'.")

                instance_handler = app.handler.get('handlers', 'instance', setup=True)
                rid, cmd_data = instance_handler.dispatch(args=data['args'], signals=data['signals'],
                                                          timeout=data['timeout'], working_dir=data['working_dir'])

                return jsonify({'rid': rid, 'cmd': cmd_data.to_dict()})
            except SynapserError as se:
                return {"error": str(se)}, 500
            except BadRequestError as bre:
                return {"error": str(bre)}, 400

        return {"error": "Request must be JSON"}, 415

    app.extend('api_ma', ma)
    app.extend('api', api)


def load(app):
    app.hook.register('post_setup', setup_api)
