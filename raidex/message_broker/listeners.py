from contextlib import contextmanager
from raidex.message_broker.message_broker import MessageBroker
from raidex import messages
from raidex.raidex_node.offer_book import OrderBookEntry
from raidex.raidex_node.order.offer import OrderType, BasicOffer
from raidex.raidex_node.order.limit_order import LimitOrder, LimitOrderFactory
from raidex.raidex_node.trades import SwapCompleted


@contextmanager
def listener_context(listener_task):
    listener_task.start()
    yield listener_task
    listener_task.stop()


class MessageListener(object):
    """Represents a listener currently listening for new messages"""

    def __init__(self, message_broker, topic='broadcast'):
        # type: (MessageBroker, str) -> None
        self.message_broker = message_broker
        self.topic = topic
        self.listener = None

    def get(self, *args, **kwargs):
        """Gets the next message or blocks until there is one

        can only be called after start()
        For parameters see gevents AsyncResult.get()
        """
        return self.listener.message_queue_async.get(*args, **kwargs)

    def get_once(self):
        """starts the listener, returns one value, and stops"""
        self.start()
        result = self.get()
        self.stop()
        return result

    def start(self):
        """Starts listening for new messages"""

        self.listener = self.message_broker.listen_on(self.topic, self._transform)
        print(f"LISTEN ON TOPIC: {self.topic} , {self.__class__.__name__}")

    def stop(self):
        """Stops listening for new messages"""
        if self.listener is not None:
            self.message_broker.stop_listen(self.listener)

    def _transform(self, message):
        return message


class TakerListener(MessageListener):
    """Listens for the Taker of the offer"""

    def __init__(self, order, message_broker):
        self.order = order
        MessageListener.__init__(self, message_broker, message_broker.address)

    def _transform(self, message):
        if isinstance(message,
                      messages.ProvenOrder) and message.order.order_id == self.order.order_id:  # TODO check more
            return message
        else:
            return None


class CancellationListener(MessageListener):

    def __init__(self, offer, message_broker):
        self.offer = offer
        MessageListener.__init__(self, message_broker, message_broker.address)

    def _transform(self, message):
        if isinstance(message,
                      messages.CancellationProof):  # TODO check more
            return message
        else:
            return None


class OfferListener(MessageListener):
    """Listens for new offers"""

    def __init__(self, market, message_broker, topic='broadcast'):
        self.market = market
        MessageListener.__init__(self, message_broker, topic)

    def _transform(self, message):
        if not isinstance(message, messages.ProvenOrder):
            return None
        order_msg = message.order

        ask_token = order_msg.ask_token
        bid_token = order_msg.bid_token

        type_ = self.market.get_offer_type(ask_token, bid_token)

        if type_ is OrderType.BUY:
            base_amount, quote_amount = order_msg.ask_amount, order_msg.bid_amount
        elif type_ is OrderType.SELL:
            base_amount, quote_amount = order_msg.bid_amount, order_msg.ask_amount
        else:
            raise AssertionError("unknown market pair")

        order = LimitOrderFactory.from_message(order_msg, self.market)

        commitment_proof = message.commitment_proof
        initiator = message.sender
        return OrderBookEntry(order, initiator, commitment_proof)


class OfferTakenListener(MessageListener):
    """Listens for Taken Messages"""

    def _transform(self, message):
        if not isinstance(message, messages.OfferTaken):
            return None
        return message.offer_id


class SwapExecutionListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, messages.SwapExecution):
            return None
        return message


class TakerCommitmentListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, messages.Commitment):
            return None
        return message

class CancellationListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, messages.Cancellation):
            return None
        return message


class CommitmentListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, messages.Commitment):
            return None
        return message


class SwapCompletedListener(MessageListener):
    """ Listens for Completed Swaps to fill the Trade-book"""

    def _transform(self, message):
        if not isinstance(message, messages.SwapCompleted):
            return None
        return SwapCompleted(message.offer_id, message.timestamp)


class CommitmentProofListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, (messages.CommitmentProof, messages.CancellationProof)):
            return None
        return message
