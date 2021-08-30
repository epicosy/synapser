from sqlalchemy.exc import OperationalError

from synapser.core.database import Database
from synapser.core.exc import SynapserError


def init_database(app):
    try:
        database = Database(dialect=app.get_config('dialect'), username=app.get_config('username'),
                            password=app.get_config('password'), host=app.get_config('host'),
                            port=app.get_config('port'), database=app.get_config('database'),
                            debug=app.config.get('log.colorlog', 'database'))

        app.extend('db', database)

    except OperationalError as oe:
        raise SynapserError(oe)


def load(app):
    app.hook.register('post_setup', init_database)

