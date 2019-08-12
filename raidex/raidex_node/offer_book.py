from __future__ import print_function
import random

from sortedcontainers import SortedDict
import structlog
from raidex.utils import pex
from raidex.utils.timestamp import to_str_repr
from raidex.raidex_node.order.offer import OrderType

from eth_utils import int_to_big_endian


log = structlog.get_logger('node.offer_book')


def generate_random_offer_id():
    # generate random offer-id in the 32byte int range
    return int(random.randint(0, 2 ** 256 - 1))


class OfferDeprecated(object):
    """

    Represents an Offer from the Broadcast.
    the broadcasted offer_message stores absolute information (bid_token, ask_token, bid_amount, ask_amount)
    the Offer stores it's information relative to it's market (type,  price)


    Internally we work with relative values because:
        1) we want to easily compare prices (prices are the ultimate ordering criterion)
        2) we want to separate BUYs from SELLs
        3) traders are used to this!

    In the broadcast we work with absolute values because:
        1) asset swaps cannot be fractional
        2) we don't want to fix the permutation of the 'market' asset-pair on the message level.

    """

    def __init__(self, type_, base_amount, quote_amount, offer_id, timeout_date,
                 maker_address=None, taker_address=None, commitment_amount=1):
        assert isinstance(type_, OrderType)
        assert isinstance(base_amount, int)
        assert isinstance(quote_amount, int)
        assert isinstance(offer_id, int)
        assert isinstance(timeout_date, int)
        assert base_amount > 0
        assert quote_amount > 0
        self.offer_id = offer_id
        self.type = type_
        self.base_amount = base_amount
        self.quote_amount = quote_amount
        self.timeout_date = timeout_date
        self.maker_address = maker_address
        self.taker_address = taker_address

        self.commitment_amount = commitment_amount

    @property
    def amount(self):
        return self.base_amount

    @property
    def price(self):
        return float(self.quote_amount) / self.base_amount

    def __repr__(self):
        return "Offer<pex(id)={} amount={} price={} type={} timeout_date={}>".format(
            pex(int_to_big_endian(self.offer_id)),
            self.amount,
            self.price,
            self.type,
            to_str_repr(self.timeout_date))


class OrderBookEntry:

    def __init__(self, order, initiator, commitment_proof):
        self.order = order
        self.initiator = initiator
        self.commitment_proof = commitment_proof

    @property
    def order_id(self):
        return self.order.order_id

    @property
    def base_amount(self):
        return self.order.base_amount

    @property
    def quote_amount(self):
        return self.order.quote_amount

    @property
    def price(self):
        return self.order.price

    @property
    def timeout_date(self):
        return self.order.timeout_date


class OrderView(object):
    """
    Holds a collection of Offers in an RBTree for faster search.
    One OfferView instance holds either BUYs or SELLs

    """

    def __init__(self):
        self.order_entries = SortedDict()
        self.order_entries_by_id = dict()

    def add_order(self, entry):
        assert isinstance(entry, OrderBookEntry)

        order_id = entry.order_id
        order_price = entry.price

        # inserts in the SortedDict
        self.order_entries[(order_price, order_id)] = entry

        # inserts in the dict for retrieval by offer_id
        self.order_entries_by_id[order_id] = entry

        return order_id

    def remove_order(self, offer_id):
        if offer_id in self.order_entries_by_id:
            entry = self.order_entries_by_id[offer_id]

            # remove from the SortedDict
            del self.order_entries[(entry.price, entry.order_id)]

            # remove from the dict
            del self.order_entries_by_id[offer_id]

    def get_order_by_id(self, order_id):
        return self.order_entries_by_id.get(order_id)

    def get_orders_by_price(self, price):

        matched_orders = list()

        for order in self.order_entries.values():
            if order.price == price:
                matched_orders.append(order)
            if order.price > price:
                break

        return matched_orders

    def __len__(self):
        return len(self.order_entries)

    def __iter__(self):
        return iter(self.order_entries)

    def values(self):
        # returns list of all offers, sorted by (price, offer_id)
        return self.order_entries.values()


class OrderBook(object):

    def __init__(self):
        self.buys = OrderView()
        self.sells = OrderView()
        self.tasks = dict()

    def insert_order(self, order_entry):
        order = order_entry.order
        assert isinstance(order.order_type, OrderType)
        if order.order_type is OrderType.BUY:
            self.buys.add_order(order_entry)
        elif order.order_type is OrderType.SELL:
            self.sells.add_order(order_entry)
        else:
            raise Exception('unsupported offer-type')

        return order_entry.order_id

    def get_order_by_id(self, order_id):
        order = self.buys.get_order_by_id(order_id)
        if order is None:
            order = self.sells.get_order_by_id(order_id)
        return order

    def contains(self, order_id):
        return order_id in self.buys.order_entries_by_id or order_id in self.sells.order_entries_by_id

    def remove_order(self, order_id):
        if order_id in self.buys.order_entries_by_id:
            order_view = self.buys
        elif order_id in self.sells.order_entries_by_id:
            order_view = self.sells
        else:
            raise Exception('offer_id not found')

        order_view.remove_order(order_id)

    def get_orders_by_price(self, price, order_type):
        order_list = self.buys if order_type == OrderType.SELL else self.sells
        return order_list.get_orders_by_price(price)

    def __repr__(self):
        return "OrderBook<buys={} sells={}>".format(len(self.buys), len(self.sells))
