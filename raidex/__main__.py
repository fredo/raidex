import argparse
from gevent.event import Event
import structlog

from raidex.raidex_node.api.app import APIServer
from raidex.app import App
from raidex.constants import KOVAN_WETH_ADDRESS, CS_ADDRESS, KOVAN_RTT_ADDRESS

structlog.configure()
#':WARNING,bots.manipulator:DEBUG'


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()

    parser.add_argument('--mock-networking', action='store_true',
                        help='In-Process Trader, MessageBroker and CommitmentService')
    parser.add_argument('--keyfile', type=argparse.FileType('r'), help='path to keyfile', required=True)
    parser.add_argument('--pwfile', type=argparse.FileType('r'), help='path to pw', required=True)
    parser.add_argument("--api", action='store_true', help='Run the REST-API')
    parser.add_argument("--api-port", type=int, help='Specify the port for the api, default is 50001', default=50001)
    parser.add_argument("--offer-lifetime", type=int, help='Lifetime of offers spawned by LimitOrders', default=30)
    parser.add_argument("--broker-host", type=str, help='Specify the host for the message broker, default is localhost',
                        default='localhost')
    parser.add_argument("--broker-port", type=int, help='Specify the port for the message broker, default is 5000',
                        default=5000)
    parser.add_argument("--trader-host", type=str, help='Specify the host for the trader mock, default is localhost',
                        default='localhost')
    parser.add_argument("--trader-port", type=int, help='Specify the port for the trader mock, default is 5001',
                        default=5001, required=True)
    parser.add_argument('--bots', nargs='+', help='Start a set of (/subset of) multiple tradi'
                                                  'ng bots.\
                                                  <Options:\"liquidity\", \"random\", \"manipulator\">')
    parser.add_argument('--token-address', type=str, help='Token address of token to trade against WETH on kovan',
                        default=KOVAN_RTT_ADDRESS)

    args = parser.parse_args()

    raidex_app = App.build_default_from_config(keyfile=args.keyfile,
                                               pw_file=args.pwfile,
                                               cs_address=CS_ADDRESS,
                                               base_token_addr=args.token_address,
                                               quote_token_addr=KOVAN_WETH_ADDRESS,
                                               message_broker_host=args.broker_host,
                                               message_broker_port=args.broker_port,
                                               trader_host=args.trader_host,
                                               trader_port=args.trader_port,
                                               offer_lifetime=args.offer_lifetime)

    raidex_app.start()

    if args.api is True:
        api = APIServer('', args.api_port, raidex_app.raidex_node)
        api.start()

    stop_event.wait()  # runs forever


if __name__ == '__main__':
    main()
