import structlog

from raidex import messages
from raidex.raidex_node.listener_tasks import ListenerTask

from raidex.raidex_node.architecture.state_change import CommitmentProofStateChange, CancellationProofStateChange, NewTradeStateChange
from raidex.raidex_node.architecture.event_architecture import dispatch_state_changes
log = structlog.get_logger('node.commitment_service.tasks')


class CommitmentProofTask(ListenerTask):
    def __init__(self,commitment_proof_listener):
        super(CommitmentProofTask, self).__init__(commitment_proof_listener)

    def process(self, data):
        log.debug('Received commitment proof: {}'.format(data))
        assert isinstance(data, (messages.CommitmentProof, messages.CancellationProof))
        state_changes = []
        if isinstance(data, messages.CommitmentProof):
            commitment_event = CommitmentProofStateChange(data.commitment_sig, data)
            state_changes.append(commitment_event)

        elif isinstance(data, messages.CancellationProof):

            cancellation_state_change = CancellationProofStateChange(data)
            state_changes.append(cancellation_state_change)

        elif isinstance(data, messages.OfferTaken):

            trade_state_change = NewTradeStateChange(data.trade_id,
                                                     data.maker_order_id,
                                                     data.taker_order_id,
                                                     data.amount,
                                                     data.secret,
                                                     data.secret_hash)
            state_changes.append(trade_state_change)

        dispatch_state_changes(state_changes)

