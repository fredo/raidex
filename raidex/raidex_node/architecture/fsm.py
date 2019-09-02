from transitions.extensions.nesting import NestedState
from transitions.extensions import HierarchicalMachine as Machine


class MachineModel:

    @property
    def _unique_id(self):
        pass

    def log_state(self, *args):
        if hasattr(self, 'state'):
            print(f'Order {self._unique_id} - State Change to: {self.state}')
        if hasattr(self, 'status'):
            print(f'Status: {self.status}')


class TradeMachine(Machine):

    def set_state(self, state, model=None):
        super(TradeMachine, self).set_state(state, model)
        if isinstance(state, str):
            state = self.get_state(state)
        model.status = state.parent.name if state.parent else state.name


class TradeState(NestedState):

    def __repr__(self):
        return self.name

    @property
    def initial(self):
        if len(self.children) > 0:
            return self.children[0]
        return None

    def name(self):
        return self._name


class OrderMachine(Machine):

    def set_state(self, state, model=None):
        super(OrderMachine, self).set_state(state, model)
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