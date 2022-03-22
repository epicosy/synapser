from synapser.plugins.jgenprog import JGenProg


class JMutRepair(JGenProg):
    """JKali"""

    class Meta:
        label = 'jmutrepair'
        version = 'xyz'


def load(nexus):
    nexus.handler.register(JMutRepair)
