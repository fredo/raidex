import gevent
from eth_utils import to_normalized_address, to_checksum_address
from raidex.utils import make_address
from raidex.utils.address import encode_topic
address = make_address()

print(to_normalized_address(address))

print(to_checksum_address(address))

print(encode_topic(int(23)))
