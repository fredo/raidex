import structlog

from raidex.raidex_node.architecture.state_change import *
from raidex.raidex_node.order.limit_order import LimitOrderFactory
from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.raidex_node.transport.events import SendProvenOrderEvent
from raidex.raidex_node.matching.match import MatchFactory
from raidex.raidex_node.architecture.data_manager import DataManager
from raidex.constants import OFFER_THRESHOLD_TIME


logger = structlog.get_logger('StateChangeHandler')


def handle_state_change(raidex_node, state_change):

    data_manager = raidex_node.data_manager

    if isinstance(state_change, OfferStateChange):
        handle_offer_state_change(data_manager, state_change)
    if isinstance(state_change, OrderTimeoutStateChange):
        handle_offer_timeout(data_manager, state_change)
    if isinstance(state_change, NewLimitOrderStateChange):
        handle_new_limit_order(data_manager, state_change)
    if isinstance(state_change, CancelLimitOrderStateChange):
        handle_cancel_limit_order(data_manager, state_change)
    if isinstance(state_change, OfferPublishedStateChange):
        handle_offer_published(data_manager, state_change)
    if isinstance(state_change, TakerCallStateChange):
        handle_taker_call(data_manager, state_change)
    if isinstance(state_change, TransferReceivedStateChange):
        handle_transfer_received(data_manager, state_change)


def handle_offer_state_change(data_manager: DataManager, state_change: OfferStateChange):
    #offer = data_manager.offer_manager.get_offer(state_change.offer_id)
    order = data_manager.orders[state_change.order_id]

    if isinstance(state_change, CommitmentProofStateChange):
        handle_commitment_proof(data_manager, order, state_change)
    if isinstance(state_change, PaymentFailedStateChange):
        #offer.payment_failed()
        #logger.info(f'Offer Payment Failed: {offer.offer_id}')
        pass
    if isinstance(state_change, CancellationProofStateChange):
        handle_cancellation_proof(order, state_change)


def handle_offer_timeout(data_manager: DataManager, state_change: OrderTimeoutStateChange):
    if data_manager.offer_manager.has_offer(state_change.order_id):
        offer = data_manager.offer_manager.get_offer(state_change.order_id)
        offer.timeout()
        logger.info(f'Offer timeout: {offer.order_id}, timeout at: {state_change.timeout_date}')
    elif data_manager.matching_engine.offer_book.contains(state_change.order_id):
        data_manager.matching_engine.offer_book.remove_order(state_change.order_id)

    data_manager.timeout_handler.clean_up_timeout(state_change.order_id)


def handle_new_limit_order(data_manager: DataManager, state_change: NewLimitOrderStateChange):
    new_order = LimitOrderFactory.from_dict(state_change.data)
    data_manager.process_order(new_order)


def handle_cancel_limit_order(data_manager: DataManager, state_change: CancelLimitOrderStateChange):
    order_id = state_change.data['order_id']
    data_manager.cancel_order(order_id)


def handle_offer_published(data_manager: DataManager, event: OfferPublishedStateChange):
    order_book_entry = event.order_entry
    order_id = order_book_entry.order.order_id

    if order_id in data_manager.orders:
        order = data_manager.orders[order_id]
        order.received_offer()
    else:
        data_manager.matching_engine.offer_book.insert_order(order_book_entry)
        data_manager.timeout_handler.create_new_timeout(order_book_entry.order, OFFER_THRESHOLD_TIME)


def handle_commitment_proof(data_manager: DataManager, order, state_change: CommitmentProofStateChange):
    commitment_proof = state_change.commitment_proof

    order.receive_commitment_proof(proof=commitment_proof)
    message_target = None

    if order.order_id in data_manager.matches:
        match = data_manager.matches[order.order_id]
        match.matched()
        message_target = match.target

    dispatch_events([SendProvenOrderEvent(order, data_manager.market, message_target)])

    logger.info(f'Received Commitment Proof: {order.order_id}')


def handle_cancellation_proof(order, state_change: CancellationProofStateChange):
    cancellation_proof = state_change.cancellation_proof

    order.receive_cancellation_proof(cancellation_proof)


def handle_taker_call(data_manager: DataManager, state_change: TakerCallStateChange):

    offer_id = state_change.offer_id
    offer = data_manager.offer_manager.get_offer(offer_id)

    match = MatchFactory.maker_match(offer, state_change.initiator, state_change.commitment_proof)
    data_manager.matches[offer_id] = match
    match.matched()


def handle_transfer_received(data_manager: DataManager, state_change: TransferReceivedStateChange):

    offer_id = state_change.raiden_event.identifier

    match = data_manager.matches[offer_id]
    match.received_inbound(raiden_event=state_change.raiden_event)

    if match.offer.state == 'completed':
        data_manager.timeout_handler.clean_up_timeout(offer_id)
        from raidex.raidex_node.order import fsm_offer
        fsm_offer.remove_model(match.offer)
