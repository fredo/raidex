from raidex.raidex_node.order.offer import OrderType
from raidex.constants import DEFAULT_OFFER_LIFETIME
from raidex.utils.random import create_random_32_bytes_id
from raidex.utils.timestamp import time_plus
from raidex.raidex_node.architecture.fsm import MachineModel
from raidex.messages import OrderMessage
from raidex.raidex_node.market import TokenPair


class LimitOrderFactory:

    @classmethod
    def from_dict(cls, data):

        if 'order_id' not in data or data['order_id'] is None:
            order_id = create_random_32_bytes_id()
        else:
            order_id = data['order_id']

        if 'lifetime' not in data:
            data['lifetime'] = DEFAULT_OFFER_LIFETIME

        if data['order_type'] == 'BUY':
            order_type = OrderType.BUY
        else:
            order_type = OrderType.SELL

        order_object = LimitOrder(
            order_id=order_id,
            order_type=order_type,
            amount=data['amount'],
            price=data['price'],
            timeout_date=None,
            lifetime=data['lifetime']
        )

        from . import fsm_order
        fsm_order.add_model(order_object)
        order_object.initiating()

        return order_object

    @classmethod
    def from_message(cls, message, market):

        if not isinstance(message, OrderMessage):
            raise TypeError(f'Is not a OrderMessage: Type given: {message.__name__}')

        ask_token = message.ask_token
        bid_token = message.bid_token

        type_ = market.get_offer_type(ask_token, bid_token)

        if type_ is OrderType.BUY:
            base_amount, quote_amount = message.ask_amount, message.bid_amount
        elif type_ is OrderType.SELL:
            base_amount, quote_amount = message.bid_amount, message.ask_amount
        else:
            raise AssertionError("unknown market pair")

        price = float(quote_amount) / base_amount

        order_object = LimitOrder(
            order_id=message.order_id,
            order_type=type_,
            amount=base_amount,
            price=price,
            timeout_date=message.timeout,
            lifetime=None
        )

        return order_object


class LimitOrder(MachineModel):

    def __init__(self, order_id, order_type: OrderType, amount: int, price: int, timeout_date, lifetime: int = DEFAULT_OFFER_LIFETIME):
        self.order_id = order_id
        self.order_type = order_type
        self.amount = amount
        self.price = price
        self.lifetime = lifetime
        self.timeout_date = timeout_date if timeout_date is not None else time_plus(seconds=lifetime)
        self.corresponding_trades = dict()
        self.commitment_proof = None

    def add_trade(self, trade):
        self.corresponding_trades[trade.trade_id] = trade

    def get_open_trades(self):

        open_trades = list()

        for trades in self.corresponding_trades.values():
            if trades.status == 'open':
                open_trades.append(trades)

        return open_trades

    @property
    def _unique_id(self):
        return self.order_id

    @property
    def open(self):

        if self.status == 'open':
            return True
        return False

    @property
    def completed(self):

        if self.status == 'completed':
            return True
        return False

    @property
    def canceled(self):

        if self.status == 'canceled':
            return True
        return False

    def amount_traded(self):
        amount_traded = 0

        for trade in self.corresponding_trades.values():
            if trade.state == 'completed':
                amount_traded += trade.base_amount
        return amount_traded

    @property
    def base_amount(self):
        return self.amount

    @property
    def quote_amount(self):
        return int(self.amount * self.price)

    @property
    def buy_amount(self):
        if self.is_buy():
            return self.base_amount
        return self.quote_amount

    @property
    def sell_amount(self):
        if self.is_buy():
            return self.quote_amount
        return self.base_amount

    def is_buy(self):
        if self.order_type == OrderType.BUY:
            return True
        return False

    def is_sell(self):
        return not self.is_buy()

    @property
    def has_proof(self):
        if hasattr(self, 'commitment_proof'):
            return True
        return False

    def set_proof(self, event_data):

        if 'proof' in event_data.kwargs:
            self.commitment_proof = event_data.kwargs['proof']

    def has_trade(self, trade_id):
        return trade_id in self.corresponding_trades

    def get_trade(self, trade_id):
        return self.corresponding_trades[trade_id]
