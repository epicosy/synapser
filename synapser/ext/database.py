from sqlalchemy.exc import OperationalError

from synapser.core.database import Database
from synapser.core.exc import SynapserError

CONFIGS_MSG = "\n\t/etc/synapser/synapser.yml\n\t~/.config/synapser/synapser.yml\n~/.synapser/config/synapser.yml\n\t~/.synapser.yml"


def check_configs(app):
    try:
        configs = app.config.get_dict()
        print(configs)
        if not configs:
            app.log.error(f"Configs not loaded. Consider one of the following: {CONFIGS_MSG}")
            exit(1)
    except TypeError as te:
        app.log.error(str(te))
        exit(1)


def init_database(app):
    try:
        db_config = app.get_config('database')
        database = Database(dialect=db_config['dialect'], username=db_config['username'],
                            password=db_config['password'], host=db_config['host'],
                            port=db_config['port'], database=db_config['name'],
                            debug=app.config.get('log.colorlog', 'database'))

        app.extend('db', database)

    except OperationalError as oe:
        raise SynapserError(oe)


def load(app):
    app.hook.register('pre_setup', check_configs)
    app.hook.register('post_setup', init_database)

