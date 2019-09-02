__all__ = ['offer', 'fsm_trade', 'fsm_order', 'limit_order']

from raidex.raidex_node.order.limit_order import LimitOrder
from raidex.raidex_node.order import events as dispatch
from raidex.raidex_node.architecture.fsm import OrderMachine, OrderState, TradeMachine, TradeState, MachineModel

# Enter Methods for orders
ENTER_UNPROVED = dispatch.on_enter_unproved
ENTER_PROVED = LimitOrder.set_proof.__name__
ENTER_PUBLISHED = dispatch.on_enter_published
ENTER_CANCELLATION = dispatch.on_enter_cancellation

def is_filled(order: LimitOrder):
    return order.amount_traded == order.amount



# Enter Methods for trades
ENTER_PENDING = dispatch.on_enter_exchanging
ENTER_WAIT_FOR_REFUND = dispatch.initiate_refund

# General
AFTER_STATE_CHANGE = MachineModel.log_state.__name__

# Order States
ORDER_OPEN = OrderState('open')
ORDER_OPEN_CREATED = OrderState('created', parent=ORDER_OPEN)
ORDER_OPEN_UNPROVED = OrderState('unproved', on_enter=[ENTER_UNPROVED], parent=ORDER_OPEN)
ORDER_OPEN_PROVED = OrderState('proved', on_enter=[ENTER_PROVED], parent=ORDER_OPEN)
ORDER_OPEN_PUBLISHED = OrderState('published', on_enter=[ENTER_PUBLISHED], parent=ORDER_OPEN)
ORDER_OPEN_CANCELLATION_REQUESTED = OrderState('cancellation_requested', on_enter=[ENTER_CANCELLATION], parent=ORDER_OPEN)
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
    {'trigger': 'receive_commitment_proof',
     'source': ORDER_OPEN_UNPROVED,
     'dest': ORDER_OPEN_PROVED},
    {'trigger': 'payment_failed',
     'source': ORDER_OPEN_UNPROVED,
     'dest': ORDER_OPEN_UNPROVED},
    {'trigger': 'timeout',
     'source': ORDER_OPEN,
     'dest': ORDER_OPEN_CANCELLATION_REQUESTED},
    {'trigger': 'receive_cancellation_proof',
     'source': ORDER_OPEN,
     'dest': ORDER_CANCELED},
    {'trigger': 'received_offer',
     'source': ORDER_OPEN_PROVED,
     'dest': ORDER_OPEN_PUBLISHED},
    {'trigger': 'received_inbound',
     'source': ORDER_OPEN_PUBLISHED,
     'conditions': [is_filled],
     'dest': ORDER_COMPLETED},
]

OPEN = TradeState('open')
OPEN_CREATED = TradeState('created', parent=OPEN)
OPEN_PENDING = TradeState('pending', on_enter=[ENTER_PENDING], parent=OPEN)
OPEN_WAIT_FOR_REFUND = TradeState('received_inbound', on_enter=[ENTER_WAIT_FOR_REFUND], parent=OPEN)
COMPLETED = TradeState('completed')
TIMEOUT = TradeState('timeout')

TRADE_STATES = [
    OPEN,
    COMPLETED,
    TIMEOUT,
]

TRADE_TRANSITIONS = [

    {'trigger': 'initiating',
     'source': OPEN_CREATED,
     'dest': OPEN_PENDING},
    {'trigger': 'payment_failed',
     'source': OPEN_PENDING,
     'dest': OPEN_PENDING},
    {'trigger': 'timeout',
     'source': OPEN,
     'dest': TIMEOUT},
    {'trigger': 'received_inbound',
     'source': OPEN_PENDING,
     'dest': COMPLETED},
]


fsm_order = OrderMachine(states=ORDER_STATES,
                         transitions=ORDER_TRANSITIONS,
                         initial=ORDER_OPEN,
                         after_state_change=AFTER_STATE_CHANGE,
                         send_event=True)


fsm_trade = TradeMachine(states=TRADE_STATES,
                         transitions=TRADE_TRANSITIONS,
                         initial=OPEN,
                         after_state_change=AFTER_STATE_CHANGE,
                         send_event=True)




