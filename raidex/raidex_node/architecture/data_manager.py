import structlog

from raidex.raidex_node.order.offer_manager import OfferManager
from raidex.raidex_node.matching.matching_engine import MatchingEngine
from raidex.raidex_node.order.limit_order import LimitOrder
from raidex.raidex_node.matching.match import MatchFactory
from raidex.constants import MATCHING_ALGORITHM
from raidex.exceptions import OfferTimedOutException
from raidex.utils.greenlet_helper import TimeoutHandler

logger = structlog.get_logger('StateChangeHandler')


class DataManager:

    def __init__(self, offer_book, market):

        self.offer_manager = OfferManager()
        self.market = market
        self.matching_engine = MatchingEngine(offer_book, MATCHING_ALGORITHM)
        self.orders = dict()
        self.matches = dict()
        self.timeout_handler = TimeoutHandler()

    def get_open_orders(self):
        return filter(lambda x: x.open, self.orders.values())

    def cancel_order(self, order_id):

        order = self.orders[order_id]
        open_offers = order.get_open_offers()

        print(open_offers)
        for offer in open_offers:
            offer.timeout()
            self.timeout_handler.clean_up_timeout(offer)

    def timeout_offer(self, offer):

        offer.timeout()
        self.timeout_handler.clean_up_timeout(offer.order_id)

    def process_order(self, order: LimitOrder):
        self.orders[order.order_id] = order
        print(f"added order {order.order_id}")
        matching_offer_entries, amount_left = self.matching_engine.match_new_order(order)

        for offer_entry in matching_offer_entries:
            take_offer = self.offer_manager.create_take_offer(offer_entry.offer)

            if self.timeout_handler.create_new_timeout(take_offer):
                taker_match = MatchFactory.taker_match(take_offer, offer_entry)
                self.matches[take_offer.order_id] = taker_match
                order.add_trade(take_offer)
                self.matching_engine.offer_book.remove_order(take_offer.order_id)
            else:
                raise OfferTimedOutException

        if amount_left > 0:
            self.timeout_handler.create_new_timeout(order)

            #make_offer = self.offer_manager.create_make_offer(order, amount_left)
            #self.timeout_handler.create_new_timeout(make_offer)
            #order.add_offer(make_offer)

