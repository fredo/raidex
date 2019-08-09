__all__ = ['offer', 'fsm_offer', 'limit_order']

from transitions.extensions.nesting import NestedState
from transitions.extensions import HierarchicalMachine as Machine

from raidex.raidex_node.order.offer import Offer
from raidex.raidex_node.order import events as dispatch

ENTER_UNPROVED = dispatch.on_enter_unproved
ENTER_PUBLISHED = dispatch.on_enter_published
ENTER_PROVED = Offer.set_proof.__name__
ENTER_CANCELLATION = dispatch.on_enter_cancellation
ENTER_WAIT_FOR_REFUND = dispatch.initiate_refund
AFTER_STATE_CHANGE = Offer.log_state.__name__


class OrderMachine(Machine):

    def set_state(self, state, model=None):
        super(OfferMachine, self).set_state(state, model)
        if isinstance(state, str):
            state = self.get_state(state)
        model.status = state.parent.name if state.parent else state.name


class OrderState(NestedState):

    def __repr__(self):
        return self.name

    @property
    def initial(self):
        if len(self.children) > 0:
            return self.children[0]
        return None

    def name(self):
        return self._name


OPEN = OrderState('open')
OPEN_CREATED = OrderState('created', parent=OPEN)
OPEN_UNPROVED = OrderState('unproved', on_enter=[ENTER_UNPROVED], parent=OPEN)
OPEN_PROVED = OrderState('proved', on_enter=[ENTER_PROVED], parent=OPEN)
OPEN_PUBLISHED = OrderState('published', on_enter=[ENTER_PUBLISHED], parent=OPEN)
OPEN_CANCELLATION_REQUESTED = OrderState('cancellation_requested', on_enter=[ENTER_CANCELLATION], parent=OPEN)
OPEN_WAIT_FOR_REFUND = OrderState('wait_for_refund', on_enter=[ENTER_WAIT_FOR_REFUND], parent=OPEN)

COMPLETED = OrderState('completed')
CANCELED = OrderState('canceled')

ORDER_STATES = [
    OPEN,
    CANCELED,
    COMPLETED,
]


ORDER_TRANSITIONS = [

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
    {'trigger': 'received_inbound',
     'source': OPEN_WAIT_FOR_REFUND,
     'dest': COMPLETED},
]


class OfferMachine(Machine):

    def set_state(self, state, model=None):
        super(OfferMachine, self).set_state(state, model)
        if isinstance(state, str):
            state = self.get_state(state)
        model.status = state.parent.name if state.parent else state.name


class OfferState(NestedState):

    def __repr__(self):
        return self.name

    @property
    def initial(self):
        if len(self.children) > 0:
            return self.children[0]
        return None

    def name(self):
        return self._name


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
                         initial=OPEN,
                         after_state_change=AFTER_STATE_CHANGE)


fsm_offer = OfferMachine(states=OFFER_STATES,
                         transitions=TRANSITIONS,
                         initial=OPEN,
                         after_state_change=AFTER_STATE_CHANGE,
                         send_event=True)




