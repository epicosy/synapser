
class SynapserError(Exception):
    """Generic errors."""
    pass


class CommandError(Exception):
    """Command error"""


class BadRequestError(Exception):
    """HTTP Bad Request Error"""
