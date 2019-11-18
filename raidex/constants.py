from eth_utils import keccak
from raidex.raidex_node.matching.matching_algorithm import match_limit

EMPTY_SECRET = bytes(32)
EMPTY_SECRET_KECCAK = keccak(EMPTY_SECRET)

DEFAULT_OFFER_LIFETIME = 60
# seconds until timeout  external offer is seen as valid
OFFER_THRESHOLD_TIME = 10


RAIDEN_POLL_INTERVAL = 0.75

MATCHING_ALGORITHM = match_limit


DEFAULT_TESTNET = 'GOERLI'

TOKEN_ADDRESSES = dict()
TOKEN_ADDRESSES['GOERLI'] = {
    'fee': '0xe6ff467647e65e80e70597fC43a74Ea698c678A2',
    'rtt': '0xA0195E88F732ff6379642eB702302dFae6EA7bC4',
    'weth': '0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6'
}

TOKEN_ADDRESSES['KOVAN'] = {
    'fee': '0x92276aD441CA1F3d8942d614a6c3c87592dd30bb',
    'rtt': '0x92276aD441CA1F3d8942d614a6c3c87592dd30bb',
    'weth': '0xd0A1E359811322d97991E03f863a0C30C2cF029C'
}

FEE_ADDRESS = TOKEN_ADDRESSES[DEFAULT_TESTNET]['fee']
RTT_ADDRESS = TOKEN_ADDRESSES[DEFAULT_TESTNET]['rtt']
WETH_ADDRESS = TOKEN_ADDRESSES[DEFAULT_TESTNET]['weth']

CS_ADDRESS = '0xEDC5f296a70096EB49f55681237437cbd249217A'
