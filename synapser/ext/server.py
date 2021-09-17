from flask import Flask, request, jsonify
#from flask_marshmallow import Marshmallow
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

    #ma = Marshmallow(api)

    @api.route('/', methods=['GET'])
    def index():
        tool = app.handler.get('handlers', app.plugin.tool, setup=True)
        return f"{VERSION_BANNER}\nServing {app.plugin.tool}\n{tool.help().output}"

    @api.route('/stream/<rid>', methods=['GET'])
    def stream(rid):
        instance_handler = app.handler.get('handlers', 'instance', setup=True)
        instance = instance_handler.get(rid)

        if instance:
            return jsonify({'socket': instance.socket, 'status': instance.status})

        return {"error": f"Repair instance {rid} not found"}, 404

    @api.route('/repair', methods=['POST'])
    def repair():
        if request.is_json:
            data = request.get_json()

            try:
                verify_bad_request(data, keys=['signals', 'timeout', 'args', 'target'],
                                   format_error="This request was not properly formatted, must specify '{}'.")

                instance_handler = app.handler.get('handlers', 'instance', setup=True)
                rid = instance_handler.dispatch(args=data['args'], signals=data['signals'], timeout=data['timeout'],
                                                working_dir=data['working_dir'], target=data['target'])

                return jsonify({'rid': rid})
            except SynapserError as se:
                return {"error": str(se)}, 500
            except BadRequestError as bre:
                return {"error": str(bre)}, 400

        return {"error": "Request must be JSON"}, 415

    @api.route('/patches/<rid>', methods=['GET'])
    def get_patches(rid):
        try:
            instance_handler = app.handler.get('handlers', 'instance', setup=True)
            instance = instance_handler.get(rid=rid)

            if not instance:
                return {"error": f"Repair instance {rid} not found"}, 404

            tool_handler = app.handler.get('handlers', app.plugin.tool, setup=True)
            patches = tool_handler.get_patches(instance.path, target_files=[instance.target])
            return jsonify(patches)
        except SynapserError as se:
            return {"error": str(se)}, 500

    #app.extend('api_ma', ma)
    app.extend('api', api)


def load(app):
    app.hook.register('post_setup', setup_api)
