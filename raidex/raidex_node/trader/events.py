class TraderEvent:
    pass


class TransferEvent(TraderEvent):

    def __init__(self, token, target, amount, identifier):
        self.token = token
        self.target = target
        self.amount = amount
        self.identifier = identifier


class SwapInitEvent(TraderEvent):

    def __init__(self, order, trade, target):
        self.order = order
        self.trade = trade
        self.target = target



