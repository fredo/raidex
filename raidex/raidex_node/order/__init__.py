__all__ = ['offer', 'fsm_offer', 'limit_order']

from raidex.raidex_node.order.offer import Offer
from raidex.raidex_node.order import events as dispatch
from raidex.raidex_node.architecture.fsm import OrderMachine, OrderState, OfferMachine, OfferState, MachineModel

ENTER_UNPROVED = dispatch.on_enter_unproved
ENTER_PUBLISHED = dispatch.on_enter_published
ENTER_PROVED = Offer.set_proof.__name__
ENTER_CANCELLATION = dispatch.on_enter_cancellation
ENTER_WAIT_FOR_REFUND = dispatch.initiate_refund
AFTER_STATE_CHANGE = MachineModel.log_state.__name__


ORDER_OPEN = OrderState('open')
ORDER_OPEN_CREATED = OrderState('created', parent=ORDER_OPEN)
ORDER_OPEN_UNPROVED = OrderState('unproved', on_enter=[ENTER_UNPROVED], parent=ORDER_OPEN)
ORDER_OPEN_PROVED = OrderState('proved', on_enter=[ENTER_PROVED], parent=ORDER_OPEN)
ORDER_OPEN_PUBLISHED = OrderState('published', on_enter=[ENTER_PUBLISHED], parent=ORDER_OPEN)
ORDER_OPEN_CANCELLATION_REQUESTED = OrderState('cancellation_requested', on_enter=[ENTER_CANCELLATION], parent=ORDER_OPEN)
ORDER_OPEN_WAIT_FOR_REFUND = OrderState('wait_for_refund', on_enter=[ENTER_WAIT_FOR_REFUND], parent=ORDER_OPEN)

ORDER_COMPLETED = OrderState('completed')
ORDER_CANCELED = OrderState('canceled')

ORDER_STATES = [
    ORDER_OPEN,
    ORDER_CANCELED,
    ORDER_COMPLETED,
]


ORDER_TRANSITIONS = [

    {'trigger': 'initiating',
     'source': ORDER_OPEN_CREATED,
     'dest': ORDER_OPEN_UNPROVED},
    {'trigger': 'payment_failed',
     'source': ORDER_OPEN_UNPROVED,
     'dest': ORDER_OPEN_UNPROVED},
    {'trigger': 'timeout',
     'source': ORDER_OPEN,
     'dest': ORDER_OPEN_CANCELLATION_REQUESTED},
    {'trigger': 'receive_cancellation_proof',
     'source': ORDER_OPEN,
     'dest': ORDER_CANCELED},
    {'trigger': 'receive_commitment_proof',
     'source': ORDER_OPEN_UNPROVED,
     'dest': ORDER_OPEN_PROVED},
    {'trigger': 'received_offer',
     'source': ORDER_OPEN_PROVED,
     'dest': ORDER_OPEN_PUBLISHED},
    {'trigger': 'received_inbound',
     'source': ORDER_OPEN_WAIT_FOR_REFUND,
     'dest': ORDER_COMPLETED},
]

OPEN = OfferState('open')
OPEN_CREATED = OfferState('created', parent=OPEN)
OPEN_UNPROVED = OfferState('unproved', on_enter=[ENTER_UNPROVED], parent=OPEN)
OPEN_PROVED = OfferState('proved', on_enter=[ENTER_PROVED], parent=OPEN)
OPEN_PUBLISHED = OfferState('published', on_enter=[ENTER_PUBLISHED], parent=OPEN)
OPEN_CANCELLATION_REQUESTED = OfferState('cancellation_requested', on_enter=[ENTER_CANCELLATION], parent=OPEN)

PENDING = OfferState('pending')
PENDING_EXCHANGING = OfferState('exchanging', parent=PENDING)
PENDING_WAIT_FOR_REFUND = OfferState('wait_for_refund', on_enter=[ENTER_WAIT_FOR_REFUND], parent=PENDING)

COMPLETED = OfferState('completed')
CANCELED = OfferState('canceled')


OFFER_STATES = [
    OPEN,
    PENDING,
    CANCELED,
    COMPLETED,
]

TRANSITIONS = [

    {'trigger': 'initiating',
     'source': OPEN_CREATED,
     'dest': OPEN_UNPROVED},
    {'trigger': 'payment_failed',
     'source': OPEN_UNPROVED,
     'dest': OPEN_UNPROVED},
    {'trigger': 'timeout',
     'source': OPEN,
     'dest': OPEN_CANCELLATION_REQUESTED},
    {'trigger': 'receive_cancellation_proof',
     'source': OPEN,
     'dest': CANCELED},
    {'trigger': 'receive_commitment_proof',
     'source': OPEN_UNPROVED,
     'dest': OPEN_PROVED},
    {'trigger': 'received_offer',
     'source': OPEN_PROVED,
     'dest': OPEN_PUBLISHED},
    {'trigger': 'found_match',
     'source': OPEN_PUBLISHED,
     'dest': PENDING_EXCHANGING},
    {'trigger': 'found_match',
     'source': OPEN_PROVED,
     'dest': PENDING_EXCHANGING},
    {'trigger': 'received_inbound',
     'source': PENDING_EXCHANGING,
     'dest': PENDING_WAIT_FOR_REFUND},
    {'trigger': 'received_inbound',
     'source': PENDING_WAIT_FOR_REFUND,
     'dest': COMPLETED},
]

fsm_order = OrderMachine(states=ORDER_STATES,
                         transitions=ORDER_TRANSITIONS,
                         initial=ORDER_OPEN,
                         after_state_change=AFTER_STATE_CHANGE,
                         send_event=True)


fsm_offer = OfferMachine(states=OFFER_STATES,
                         transitions=TRANSITIONS,
                         initial=OPEN,
                         after_state_change=AFTER_STATE_CHANGE,
                         send_event=True)




