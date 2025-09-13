from __future__ import annotations
from typing import List, Tuple
import hashlib, re

def shingle_tokens(text: str, n: int = 7) -> List[str]:
    toks = [t.lower() for t in re.findall(r'\w+', text)]
    return [' '.join(toks[i:i+n]) for i in range(0, max(0, len(toks)-n+1))]

def minhash_signature(shingles: List[str], num_perm: int = 128) -> List[int]:
    sig = [2**63-1] * num_perm
    for s in shingles:
        bs = s.encode('utf-8')
        for p in range(num_perm):
            h = hashlib.blake2b(bs, digest_size=8, person=str(p).encode()).digest()
            val = int.from_bytes(h, 'big')
            if val < sig[p]:
                sig[p] = val
    return sig

def jaccard_from_signatures(sig1: List[int], sig2: List[int]) -> float:
    if not sig1 or not sig2: return 0.0
    same = sum(1 for a,b in zip(sig1, sig2) if a==b)
    return same / len(sig1)

def cluster_near_duplicates(items: List[Tuple[str, str]], ngram: int, num_perm: int, threshold: float):
    sigs = {}
    for k, text in items:
        sigs[k] = minhash_signature(shingle_tokens(text, n=ngram), num_perm=num_perm)
    keys = list(sigs.keys())
    clusters: List[List[str]] = []
    seen = set()
    for i, a in enumerate(keys):
        if a in seen: continue
        cluster = [a]; seen.add(a)
        for j in range(i+1, len(keys)):
            b = keys[j]
            if b in seen: continue
            if jaccard_from_signatures(sigs[a], sigs[b]) >= threshold:
                cluster.append(b); seen.add(b)
        clusters.append(cluster)
    return clusters