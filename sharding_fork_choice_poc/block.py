from tools import to_hex, sha3, hash_to_int, checkpow
import os


class MainChainBlock():
    def __init__(self, parent, pownonce, ts, powdiff):
        self.parent_hash = parent.hash if parent else (b'\x00' * 32)
        assert isinstance(self.parent_hash, bytes)
        self.hash = sha3(self.parent_hash + str(pownonce).encode('utf-8'))
        self.ts = ts
        if parent:
            assert checkpow(parent.pownonce, pownonce, powdiff)
            assert self.ts >= parent.ts
        self.pownonce = pownonce
        self.number = 0 if parent is None else parent.number + 1


# Not a full RANDAO; stub for now
class BeaconBlock():
    def __init__(self, parent, proposer, ts, sigs, main_chain_ref, nb_notaries, nb_shards, sample = 9, min_sample = 5, base_ts_diff=1, skip_ts_diff=6):
        self.contents = os.urandom(32)
        self.parent_hash = parent.hash if parent else (b'\x11' * 32)
        self.hash = sha3(self.parent_hash + self.contents)
        self.ts = ts
        self.sigs = sigs
        self.number = parent.number + 1 if parent else 0
        self.main_chain_ref = main_chain_ref.hash if main_chain_ref else parent.main_chain_ref

        if parent:
            i = parent.child_proposers.index(proposer)
            assert self.ts >= parent.ts + base_ts_diff + i * skip_ts_diff
            assert len(sigs) >= parent.notary_req
            for sig in sigs:
                assert sig.target_hash == self.parent_hash

        # Calculate child proposers
        v = hash_to_int(sha3(self.contents))
        self.child_proposers = []
        while v > 0:
            self.child_proposers.append(v % nb_notaries)
            v //= nb_notaries

        # Calculate notaries
        first = parent and proposer == parent.child_proposers[0]
        self.notary_req = 0 if first else min_sample
        v = hash_to_int(sha3(self.contents + b':n'))
        self.notaries = []
        for i in range(sample if first else sample):
            self.notaries.append(v % nb_notaries)
            v //= nb_notaries

        # Calculate shard proposers
        v = hash_to_int(sha3(self.contents + b':s'))
        self.shard_proposers = []
        for i in range(nb_shards):
            self.shard_proposers.append(v % nb_notaries)
            v //= nb_notaries


class ShardCollation():
    def __init__(self, shard_id, parent, proposer, beacon_ref, ts):
        self.proposer = proposer
        self.parent_hash = parent.hash if parent else (bytes([40 + shard_id]) * 32)
        self.hash = sha3(self.parent_hash + str(self.proposer).encode('utf-8') + beacon_ref.hash)
        self.ts = ts
        self.shard_id = shard_id
        self.number = parent.number + 1 if parent else 0
        self.beacon_ref = beacon_ref.hash

        if parent:
            assert self.shard_id == parent.shard_id
            assert self.proposer == beacon_ref.shard_proposers[self.shard_id]
            assert self.ts >= parent.ts

        assert self.ts >= beacon_ref.ts


class BlockMakingRequest():
    def __init__(self, parent, ts):
        self.parent = parent
        self.ts = ts
        self.hash = os.urandom(32)


class Sig():
    def __init__(self, proposer, target):
        self.proposer = proposer
        self.target_hash = target.hash
        self.hash = os.urandom(32)
        assert self.proposer in target.notaries

