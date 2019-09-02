from raidex.raidex_node.architecture.fsm import MachineModel
from raidex.utils.random import create_random_32_bytes_id, random_secret
from eth_utils import keccak


class TradeFactory:

    @classmethod
    def make_trade(cls, make_order_id, take_order_id, amount):

        trade_id = create_random_32_bytes_id()
        secret = random_secret()
        secret_hash = keccak(secret)

        return Trade(trade_id=trade_id,
                     maker_order_id=make_order_id,
                     taker_order_id=take_order_id,
                     amount=amount,
                     timeout_date=None,
                     secret=secret,
                     secret_hash=secret_hash)


class Trade(MachineModel):

    def __init__(self, trade_id, maker_order_id, taker_order_id, amount, timeout_date, secret=None, secret_hash=None):
        self.trade_id = trade_id
        self.maker_order_id = maker_order_id
        self.taker_order_id = taker_order_id
        self.amount = amount
        self.timeout_date = timeout_date
        self.secret = secret
        self.secret_hash = secret_hash

    @property
    def _unique_id(self):
        return self.trade_id

    def is_maker(self, order_id):
        return True if self.maker_order_id == order_id else False

    def is_taker(self, order_id):
        return True if self.taker_order_id == order_id else False

