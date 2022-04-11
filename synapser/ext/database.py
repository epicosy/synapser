import subprocess

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


def exec_cmd(app, cmd: str, msg: str):
    with subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as proc:
        app.log.info(msg)
        out = []
        for line in proc.stdout:
            decoded = line.decode()
            out.append(decoded)
            app.log.info(decoded)

        proc.wait(timeout=1)

        if proc.returncode and proc.returncode != 0:
            proc.kill()
            err = proc.stderr.read().decode()

            if err:
                app.log.error(err)
                exit(proc.returncode)

    return ''.join(out)


def start_psql_server(app):
    """
        Verifies if postgresql server is down and starts it.

        :param app: application object
    """
    # check postgresql server status
    output = exec_cmd(app, "/etc/init.d/postgresql status", msg="Checking postgresql server status")

    if 'down' in output:
        # start postgresql
        exec_cmd(app, "/etc/init.d/postgresql start", msg="Starting postgresql server")


def init_database(app):
    try:
        db_config = app.get_config('database')
        start_psql_server(app)
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

