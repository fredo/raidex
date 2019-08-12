from gevent import spawn_later, kill

from raidex.raidex_node.architecture.state_change import OrderTimeoutStateChange
from raidex.exceptions import AlreadyTimedOutException
from raidex.raidex_node.architecture.event_architecture import dispatch_state_changes
from raidex.utils.timestamp import time_plus, seconds_to_timeout, to_seconds


def future_timeout(order, threshold=0):

    spawn_time = seconds_to_timeout(order.timeout_date)-threshold
    timeout_state_change = OrderTimeoutStateChange(order.order_id, order.timeout_date)
    print(f'SPAWN TIME OF {order.order_id} in {spawn_time} seconds, seconds to timeout: {seconds_to_timeout(order.timeout_date)-threshold}')
    return spawn_later(spawn_time, dispatch_state_changes, timeout_state_change)


def kill_greenlet(greenlet):
    kill(greenlet)


class TimeoutHandler:

    def __init__(self):
        self.timeout_greenlets = dict()

    def create_new_timeout(self, order, threshold=0):

        order_id = order.order_id

        if self._has_greenlet(order_id) and not self._is_still_alive(order_id):
            raise AlreadyTimedOutException()

        self.clean_up_timeout(order_id)
        timeout_greenlet = future_timeout(order, threshold)
        self.timeout_greenlets[order_id] = timeout_greenlet
        return True

    def _has_greenlet(self, order_id):
        if order_id in self.timeout_greenlets:
            return True
        return False

    def _is_still_alive(self, order_id):

        if order_id in self.timeout_greenlets and not self.timeout_greenlets[order_id].dead:
            return True
        return False

    def clean_up_timeout(self, order_id):

        if order_id in self.timeout_greenlets:
            kill_greenlet(self.timeout_greenlets[order_id])
            del self.timeout_greenlets[order_id]
