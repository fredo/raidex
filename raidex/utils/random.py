import os
from uuid import uuid4
from raidex.constants import EMPTY_SECRET


def create_random_32_bytes_id():
    return int(uuid4().int % (2 ** 32 - 1))


def random_secret():
    """ Return a random 32 byte secret except the 0 secret since it's not accepted in the contracts
    """
    while True:
        secret = os.urandom(32)
        if secret != EMPTY_SECRET:
            return secret
