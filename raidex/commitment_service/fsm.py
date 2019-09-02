from raidex.raidex_node.architecture.fsm import TradeState, TradeMachine


INITIATED = TradeState('initiated')
RECEIVED_MAKER_SUCCESS = TradeState('received_maker_success')
RECEIVED_TAKER_SUCCESS = TradeState('received_taker_success')
COMPLETED = TradeState('completed')
TIMEOUT = TradeState('timeout')

STATES = [
    INITIATED,
    RECEIVED_MAKER_SUCCESS,
    RECEIVED_TAKER_SUCCESS,
    COMPLETED,
    TIMEOUT,
]

TRANSITIONS = [
    {'trigger': 'success_message',
     'conditions': ['is_maker'],
     'source': INITIATED,
     'dest': RECEIVED_MAKER_SUCCESS},
    {'trigger': 'success_message',
     'conditions': ['is_taker'],
     'source': INITIATED,
     'dest': RECEIVED_TAKER_SUCCESS},
    {'trigger': 'success_message',
     'conditions': ['is_taker'],
     'source': RECEIVED_MAKER_SUCCESS,
     'dest': COMPLETED},
    {'trigger': 'success_message',
     'conditions': ['is_maker'],
     'source': RECEIVED_TAKER_SUCCESS,
     'dest': COMPLETED},
    {'trigger': 'timeout',
     'source': [INITIATED, RECEIVED_MAKER_SUCCESS, RECEIVED_TAKER_SUCCESS],
     'dest': TIMEOUT},
]

fsm_trade = TradeMachine(states=STATES,
                         transitions=TRANSITIONS,
                         initial=INITIATED,
                         send_event=True)