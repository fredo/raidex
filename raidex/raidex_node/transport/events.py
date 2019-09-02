from raidex.utils.timestamp import time_int, time_plus
from raidex.raidex_node.order.offer import OrderType
from raidex.raidex_node.order.limit_order import LimitOrder
from raidex.raidex_node.market import TokenPair
import raidex.messages as message_format


class TransportEvent:
    pass


class SignMessageEvent:
    pass


class SendMessageEvent(TransportEvent):

    def __init__(self, target, message=None):
        self.target = target
        self._message = message

    @property
    def message(self):
        if self._message is None:
            self._message = self._generate_message()
        return self._message

    def _generate_message(self):
        raise NotImplementedError


class BroadcastEvent(SendMessageEvent):

    def __init__(self, message):
        super(BroadcastEvent, self).__init__('broadcast', message)

    def _generate_message(self):
        raise NotImplementedError


class SendProvenOrderEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, order, market, target='broadcast'):
        target = target if target is not None else 'broadcast'
        super(SendProvenOrderEvent, self).__init__(target)
        self.order = order
        self.market = market

    def _generate_message(self):
        order_msg = _create_order_msg(self.order, self.market)
        return message_format.ProvenOrder(order_msg, self.order.commitment_proof)


class CancellationEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, target, offer_id):
        super(CancellationEvent, self).__init__(target)
        self.offer_id = offer_id

    def _generate_message(self):
        return message_format.Cancellation(self.offer_id)


class CommitmentEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, target, order, commitment_amount, market):
        super(CommitmentEvent, self).__init__(target)
        self.order = order
        self.market = market
        self.commitment_amount = commitment_amount

    def _generate_message(self):

        order_msg = _create_order_msg(self.order, self.market)
        return message_format.Commitment(self.order.order_id,
                                         order_msg.hash,
                                         self.order.timeout_date,
                                         self.commitment_amount,
                                         [])


class SendExecutedEventEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, target, order_id, trade_id):
        super(SendExecutedEventEvent, self).__init__(target)
        self.order_id = order_id
        self.trade_id = trade_id
        self.timestamp_ = time_int()

    def _generate_message(self):
        return message_format.SwapExecution(self.order_id, self.trade_id, self.timestamp_)


def _create_order_msg(order, market):
    # type: (LimitOrder, TokenPair) -> message_format.OrderMessage

    timeout_date = order.timeout_date

    if order.order_type == OrderType.SELL:
        return message_format.OrderMessage(market.quote_token,
                                           order.quote_amount,
                                           market.base_token,
                                           order.base_amount,
                                           order.order_id,
                                           timeout_date)
    else:
        return message_format.OrderMessage(market.base_token,
                                           order.base_amount,
                                           market.quote_token,
                                           order.quote_amount,
                                           order.order_id,
                                           timeout_date)
