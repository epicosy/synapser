from synapser.plugins.jgenprog import JGenProg


class JKali(JGenProg):
    """JKali"""

    class Meta:
        label = 'jkali'
        version = 'xyz'


def load(nexus):
    nexus.handler.register(JKali)
