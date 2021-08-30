from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow


def setup_api(app):
    api = Flask('synapser')
    api.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    api.config["SQLALCHEMY_DATABASE_URI"] = app.db.engine.url
    ma = Marshmallow(api)

    @api.route('/repair', methods=['POST'])
    def repair():
        instance_handler = app.handler.get('handlers', 'instance', setup=True)
        iid, cmd_data = instance_handler.dispatch(args=request.form['args'], test_command=request.form['test_command'],
                                                  compiler_command=request.form['compiler_command'],
                                                  timeout=request.form['timeout'],
                                                  benchmark_endpoint=request.form['benchmark_endpoint'])
        results = {'iid': iid}
        results.update(cmd_data.to_dict())
        return jsonify(results)

    app.extend('api_ma', ma)
    app.extend('api', api)


def load(app):
    app.hook.register('post_setup', setup_api)
