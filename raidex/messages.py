import json
import base64

from copy import deepcopy
import rlp
from rlp.sedes import BigEndianInt, Binary
from eth_utils import (keccak, big_endian_to_int, int_to_big_endian, encode_hex, decode_hex)
from eth_keys import keys
from raidex.utils import pex
from raidex.utils import timestamp


sig65 = Binary.fixed_length(65, allow_empty=True)
address = Binary.fixed_length(20, allow_empty=True)
contract_address = Binary.fixed_length(42, allow_empty=True)
int32 = BigEndianInt(32)
int256 = BigEndianInt(256)
hash32 = Binary.fixed_length(32)
trie_root = Binary.fixed_length(32, allow_empty=True)


def sign(messagedata, private_key):
    if not isinstance(private_key, keys.PrivateKey):
        privkey_instance = keys.PrivateKey(private_key)
    else:
        privkey_instance = private_key
    return privkey_instance.sign_msg(messagedata).to_bytes()


class RLPHashable(rlp.Serializable):
    # _cached_rlp caches serialized object

    _mutable = True

    priority = 0

    fields = [('cmdid', int32)]

    @property
    def hash(self):
        return keccak(rlp.encode(self))  # this was `cached=True`, but made the obj immutable e.g. on every comparison

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.hash == other.hash

    def __hash__(self):
        return big_endian_to_int(self.hash)

    def __lt__(self, other):
        return self.priority < other.priority

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        #try:
        h = self.hash
        #except Exception:
        #   h = b''
        return '<%s(%s)>' % (self.__class__.__name__, pex(h))


class SignatureMissingError(Exception):
    pass


class Signed(RLPHashable):

    _sender = ''
    # signature = ''
    fields = [('signature', sig65)] + RLPHashable.fields

    #def __init__(self, sender=''):
    #    assert not sender or isaddress(sender)
    #    super(Signed, self).__init__(sender=sender)

    def __len__(self):
        return len(rlp.encode(self))

    @property
    def hash(self):
        if self.signature is None:
            return self._hash_without_signature
        return super(Signed, self).hash

    @property
    def _hash_without_signature(self):
        return keccak(rlp.encode(self, self.__class__.exclude(['signature'])))

    def sign(self, privkey):
        assert self.is_mutable()
        assert isinstance(privkey, bytes) and len(privkey) == 32
        self.signature = sign(self._hash_without_signature, privkey)
        self.make_immutable()
        return self

    @property
    def has_sig(self):
        if Binary.is_valid_type(self.signature) and sig65.is_valid_length(len(self.signature)):
            return True
        else:
            return False

    @property
    def sender(self):
        if not self._sender:
            if not self.signature:
                raise SignatureMissingError()
            if isinstance(self.signature, bytes):
                signature_obj = keys.Signature(signature_bytes=self.signature)
            else:
                signature_obj = self.signature
            pub = signature_obj.recover_public_key_from_msg(self._hash_without_signature)
            self._sender = decode_hex(pub.to_address())
        return self._sender

    @classmethod
    def deserialize(cls, serial, exclude=[], **kwargs):

        obj = super(Signed, cls).deserialize(serial, exclude, **kwargs)
        if not obj.has_sig:
            obj.__dict__['_mutable'] = False  # TODO checkme if this is good/valid?
            # reason - for remote signing of messages this is very handy
            # one can sign a message if it doesn't have a sig yet, even when the obj
            # comes from deserialization
        return obj


class OrderMessage(RLPHashable):
    """An `SwapOffer` is the base for a `ProvenOffer`. Its `offer_id`, `hash` and `timeout` should be sent
    as a `Commitment` to a commitment service provider.

    Data:
        offer = rlp([ask_token, ask_amount, bid_token, bid_amount, offer_id, timeout])
        timeout = <UTC milliseconds since epoch>
        offer_sig = sign(keccak(offer), maker)

    Broadcast:
        {
            "msg": "offer",
            "version": 1,
            "data": "rlp([offer])" XXX
        }
    """

    fields = [
        ('ask_token', address),
        ('ask_amount', int256),
        ('bid_token', address),
        ('bid_amount', int256),
        ('order_id', int32),  # arbitrarily chosen by node, bestcase: randomly chosen
        ('timeout', int256),
    ] + RLPHashable.fields

    def __init__(self, ask_token, ask_amount, bid_token, bid_amount, order_id, timeout, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)

        super(OrderMessage, self).__init__(ask_token, ask_amount, bid_token, bid_amount, order_id, timeout, cmdid)

    def timed_out(self, at=None):
        if at is None:
            at = timestamp.time_int()
        return self.timeout < at

    def __repr__(self):
        try:
            h = self.hash
        except Exception:
            h = b''
        return '<%s(%s) ask: %s[%s] bid %s[%s] h:%s>' % (
            self.__class__.__name__,
            pex(int_to_big_endian(self.offer_id)),
            pex(self.ask_token),
            self.ask_amount,
            pex(self.bid_token),
            self.bid_amount,
            pex(h),
        )


class Commitment(Signed):

    fields = [
        ('order_id', int32), # FIXME we should reference Swaps with the offer_hash!
        ('order_hash', hash32),
        ('timeout', int256),
        ('amount', int256),
    ] + Signed.fields

    def __init__(self, order_id, order_hash, timeout, amount, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(Commitment, self).__init__(order_id, order_hash, timeout, amount, signature, cmdid)


class OfferTaken(Signed):
    """ The CommitmentService publishes this offer on the broadcast as soon as an engaged (commited) Taker
    is determined by the CS so that it doesn't receive any incoming Raiden transfers for that offer anymore.

    Data:
        offer_id = offer_id
        offer_hash = keccak(offer)

        Broadcast:
        {
            "msg": "offer_taken",
            "version": 1,
            "data": rlp([offer_id, offer_hash)
        }

    """

    fields = [
        ('offer_id', int32),
    ] + Signed.fields

    def __init__(self, offer_id, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(OfferTaken, self).__init__(offer_id, signature, cmdid)


class CommitmentProof(Signed):
    """A `CommitmentProof` is the commitment service's signature that a commitment was made. It allows
        maker and taker to confirm each other's commitment to the swap.
        Data:
            commitment_sig = sign(commitment, committer)
            proof = sign(commitment_sig, cs)
        Broadcast:
            {
                "msg": "commitment_proof",
                "version": 1,
                "data": rlp(commitment_sig, proof)
            }
    """

    fields = [
        ('commitment_sig', sig65),
        ('secret', hash32),
        ('secret_hash', hash32),
        ('offer_id', int32)
    ] + Signed.fields

    def __init__(self, commitment_sig, secret, secret_hash, offer_id, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(CommitmentProof, self).__init__(commitment_sig, secret, secret_hash, offer_id, signature, cmdid)


class Cancellation(Signed):

    fields = [
        ('offer_id', int32),
    ] + Signed.fields

    def __init__(self, offer_id, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(Cancellation, self).__init__(offer_id, signature, cmdid)


class CancellationProof(Signed):

    fields = [
        ('offer_id', int32),
        ('cancellation_proof', CommitmentProof)
    ] + Signed.fields

    def __init__(self, offer_id, cancellation_proof, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(CancellationProof, self).__init__(offer_id, cancellation_proof, signature, cmdid)


class ProvenOffer(Signed):
    """A `ProvenOffer` is published by a market maker and pushed to one ore more broadcast services.
    A taker should recover the commitment service address from the `commitment_proof` and commit to it, if
    they want to engage in the swap.

    Data:
        offer = rlp([ask_token, ask_amount, bid_token, bid_amount, offer_id, timeout])
        timeout = <UTC milliseconds since epoch>
        offer_sig = sign(keccak(offer), maker)
        commitment = rlp([offer_id, keccak(offer), timeout, amount])
        commitment_sig = raiden signature of the commitment transfer by the committer
        commitment_proof = sign(commitment_sig, cs)

    Broadcast:
        {
            "msg": "offer",
            "version": 1,
            "data": "rlp([offer, commitment, commitment_proof])"
        }
    """
    fields = [
        ('offer', OrderMessage),
        ('commitment_proof', CommitmentProof),
    ] + Signed.fields

    def __init__(self, offer, commitment_proof, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(ProvenOffer, self).__init__(offer, commitment_proof, signature, cmdid)


class ProvenCommitment(Signed):
    """A `ProvenCommitment` is sent from taker to maker to confirm that the taker has sucessfully engaged in
     the swap by having a proper Commitment open at the makers commitment-service to execute the swap.

    Data:
        commitment = rlp([offer_id, keccak(offer), timeout, amount])
        commitment_sig = raiden signature of the commitment transfer by the committer
        commitment_proof = sign(commitment_sig, cs)

    Broadcast:
        {
            "msg": "offer",
            "version": 1,
            "data": "rlp([offer, commitment, commitment_proof])"
        }
    """
    fields = [
        ('commitment', Commitment),
        ('commitment_proof', CommitmentProof),
    ] + Signed.fields

    def __init__(self, commitment, commitment_proof, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(ProvenCommitment, self).__init__(commitment, commitment_proof, signature, cmdid)


class CommitmentServiceAdvertisement(Signed):
    """A `CommitmentServiceAdvertisement` can be send by the Commitment Service (CS) to broadcast services
    in order to announce its service to users.

    Data:
        address = <ethereum/raiden address>
        commitment_asset = <asset_address of the accepted commitment currency>
        fee_rate = <uint32 (fraction of uint32.max_int)>

    Broadcast:
        {
            "msg": "commitment_service",
            "data": rlp([address, commitment_asset, fee_rate]),
            "version": 1
        }

    Fee calculations:

    Users of the service have to expect to have a fee of e.g.

    uint32_maxint = 2 ** 32
    fee = int(float_fee_rate/uint32_maxint * commitment_in_wei + .5)

    mock fee: random.randint(1, 100000) # wei
    mock fee_rate: int(random.random() * uint32_maxint)

    deducted from each commitment.
    """

    fields = [
        # FIXME address field redundant
        ('address', address),
        ('commitment_asset', address),
        ('fee_rate', int32),
    ] + Signed.fields

    def __init__(self, address, commitment_asset, fee_rate, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(CommitmentServiceAdvertisement, self).__init__(address, commitment_asset, fee_rate, signature, cmdid)


class SwapExecution(Signed):
    """`SwapExecution` is used by both parties of a swap, in order to confirm to the CS that the swap
    went through and have the committed tokens released.

    Data:
        offer_id = offer.offer_id
        timestamp = int256 <unix timestamp (ms) of the successful execution of the swap>

    Broadcast:
        {
            "msg": "swap_execution",
            "version": 1,
            "data": rlp([offer_id, timestamp])
        }
    """

    fields = [
        ('offer_id', int256),
        ('timestamp', int256),
    ] + Signed.fields

    def __init__(self, offer_id, timestamp, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(SwapExecution, self).__init__(offer_id, timestamp, signature, cmdid)


class SwapCompleted(SwapExecution):
    """`SwapCompleted` can be used by the commitment service after a successful swap,
    in order to build its reputation.

    Data:
        offer_id = offer.offer_id
        timestamp = int256 <unix timestamp (ms) of the last swap confirmation>

    Broadcast:
        {
            "msg": "swap_completed",
            "version": 1,
            "data": rlp([offer_id, timestamp])
        }
    """

    def __init__(self, offer_id, timestamp, signature=None, cmdid=None):
        cmdid = get_cmdid_for_class(self.__class__)
        super(SwapCompleted, self).__init__(offer_id, timestamp, signature, cmdid)


msg_types_map = dict(
        offer=OrderMessage,
        proven_offer=ProvenOffer,
        proven_commitment=ProvenCommitment,
        commitment=Commitment,
        commitment_proof=CommitmentProof,
        commitment_service=CommitmentServiceAdvertisement,
        swap_executed=SwapExecution,
        swap_completed=SwapCompleted,
        offer_taken=OfferTaken,
        cancellation=Cancellation,
        cancellation_proof=CancellationProof
        )

types_msg_map = {value: key for key, value in msg_types_map.items()}

msg_cmdid_map = dict(
        offer=1,
        proven_offer=2,
        proven_commitment=3,
        commitment=4,
        commitment_proof=5,
        commitment_service=6,
        swap_executed=7,
        swap_completed=8,
        offer_taken=9,
        cancellation=10,
        cancellation_proof=11
        )


def get_cmdid_for_class(klass):
    msg = types_msg_map[klass]
    cmdid = msg_cmdid_map[msg]
    return cmdid


class Envelope(object):
    """Class to pack (`Envelope.envelop`) and unpack (`Envelope.open`) rlp messages
    in a broadcastable JSON-envelope. The rlp-data fields will be base64 encoded.
    """

    version = 1

    def __init__(self):
        pass

    @staticmethod
    def encode(data):
        return base64.encodebytes(rlp.encode(data)).decode(encoding="utf-8")

    @staticmethod
    def decode(data):
        return rlp.decode(base64.decodebytes(data.encode(encoding='utf-8')))

    @classmethod
    def open(cls, data):
        """Unpack the message data and return a message instance.
        """
        try:
            envelope = json.loads(data)
            assert isinstance(envelope, dict)
        except ValueError:
            raise ValueError("JSON-Envelope could not be decoded")

        if envelope['version'] != cls.version:
            raise ValueError("Message version mismatch! want:{} got:{}".format(
                Envelope.version, envelope['msg']))

        klass = msg_types_map[envelope['msg']]
        message = klass.deserialize(cls.decode(envelope['data']))

        return message

    @classmethod
    def envelop(cls, message):
        """Wrap the message in a json envelope.
        """
        assert isinstance(message, RLPHashable)
        envelope = dict(
                version=Envelope.version,
                msg=types_msg_map[message.__class__],
                data=cls.encode(message.serialize(message)),
                )
        return json.dumps(envelope)
