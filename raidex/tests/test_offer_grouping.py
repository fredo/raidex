import decimal

from collections import namedtuple

from raidex.raidex_node.offer_grouping import GroupedOffer, group_offers, group_trades
from raidex.utils import milliseconds
from raidex.raidex_node.trades import Trade
from raidex.raidex_node.offer_book import OfferType

Offer = namedtuple("Offer", "amount, price, timeout type_")


def test_same_offer_grouping():
    price_group_precision = 3

    offer1 = Offer(100, 0.12349, timeout=milliseconds.time_plus(1), type_=OfferType.BUY)
    offer2 = Offer(100, 0.12341, timeout=milliseconds.time_plus(1), type_=OfferType.BUY)

    # test group_offers
    grouped = group_offers([offer1, offer2], price_group_precision=price_group_precision)
    assert len(grouped) == 1


def test_different_offer_grouping():
    price_group_precision = 3

    offer1 = Offer(100, 0.123501, timeout=milliseconds.time_plus(1), type_=OfferType.BUY)
    offer2 = Offer(100, 0.123401, timeout=milliseconds.time_plus(1), type_=OfferType.BUY)

    # test group_offers
    grouped = group_offers([offer1, offer2], price_group_precision=price_group_precision)
    assert len(grouped) == 2


def test_trade_gouping():
    price_group_precision = 3
    time_group_interval_ms = 100

    offer1 = Offer(100, 0.12349, timeout=milliseconds.time_plus(1), type_=OfferType.BUY)
    offer2 = Offer(100, 0.12501, timeout=milliseconds.time_plus(1), type_=OfferType.SELL)

    # don't work with epoch based timestamps here
    trade1 = Trade(offer1, timestamp=100) # should be in 100 ms bucket
    trade2 = Trade(offer1, timestamp=199) # should be in 100 ms bucket, gets grouped with trade1
    trade3 = Trade(offer1, timestamp=201) # should be in 200 ms bucket (next highest bucket)
    trade4 = Trade(offer2, timestamp=201) # should be in 200 ms bucket, but not grouped with trade3

    grouped = group_trades([trade1, trade2, trade3, trade4], price_group_precision, time_group_interval_ms)
    assert len(grouped) == 3

    # grouped is sorted by (timestamp, price) (priority: smaller values)

    # trade1 and trade2 combined (BUY):
    assert grouped[0].amount == 200
    assert grouped[0].timestamp == 100

    # trade3 (same timestamp-bucket as trade4, but smaller price and different type) (BUY):
    assert grouped[1].amount == 100
    assert grouped[1].timestamp == 200

    # trade4 (SELL):
    assert grouped[2].amount == 100
    assert grouped[2].timestamp == 200
