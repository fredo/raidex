from raidex.raidex_node.architecture.event_architecture import dispatch_events
from raidex.raidex_node.commitment_service.events import CommitEvent, CommitmentProvedEvent, ReceivedInboundEvent, CancellationRequestEvent


class OrderStateChange:

    __slots__ = [
        'offer_id',
    ]

    def __init__(self, offer_id):
        self.offer_id = offer_id


class OrderTimeoutEvent(OrderStateChange):

    __slots__ = [
        'timeout_date'
    ]

    def __init__(self, offer_id, timeout_date):
        super(OrderTimeoutEvent, self).__init__(offer_id)
        self.timeout_date = timeout_date


class CommitmentProofStateChange(OrderStateChange):

    __slots__ = [
        'commitment_signature',
        'commitment_proof'
    ]

    def __init__(self, commitment_signature, commitment_proof):
        super(CommitmentProofStateChange, self).__init__(commitment_proof.order_id)
        self.commitment_signature = commitment_signature
        self.commitment_proof = commitment_proof


def on_enter_unproved(event_data):
    dispatch_events([CommitEvent(order=event_data.model)])


def on_enter_published(event_data):
    dispatch_events([CommitmentProvedEvent(order=event_data.model)])


def initiate_refund(event_data):
    dispatch_events([ReceivedInboundEvent(order=event_data.model,
                                          raiden_event=event_data.kwargs['raiden_event'])])


def on_enter_cancellation(event_data):
    dispatch_events([CancellationRequestEvent(order=event_data.model)])
