class CommitmentServiceEvent:
    def __init__(self, order):
        self.order = order


class CommitEvent(CommitmentServiceEvent):
    pass


class CommitmentProvedEvent(CommitmentServiceEvent):
    pass


class ReceivedInboundEvent(CommitmentServiceEvent):
    def __init__(self, order, raiden_event):
        super(ReceivedInboundEvent, self).__init__(order)
        self.raiden_event = raiden_event


class CancellationRequestEvent(CommitmentServiceEvent):
    pass
