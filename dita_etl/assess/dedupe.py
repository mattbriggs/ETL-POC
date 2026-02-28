"""Near-duplicate detection via MinHash — pure functions.

Uses token n-gram shingling and MinHash signatures to efficiently cluster
documents that are likely near-duplicates without comparing every pair of
full texts.

All functions are pure: no I/O, no side effects.
"""

from __future__ import annotations

import hashlib
import re


def shingle_tokens(text: str, n: int = 7) -> list[str]:
    """Tokenise *text* and return all overlapping n-gram shingles.

    :param text: Input document text.
    :param n: Shingle size (token n-gram window).
    :returns: List of n-gram strings, lower-cased and space-separated.

    :Example:

    .. code-block:: python

        shingles = shingle_tokens("the quick brown fox", n=2)
        # ["the quick", "quick brown", "brown fox"]
    """
    tokens = [t.lower() for t in re.findall(r"\w+", text)]
    return [
        " ".join(tokens[i: i + n])
        for i in range(max(0, len(tokens) - n + 1))
    ]


def minhash_signature(shingles: list[str], num_perm: int = 128) -> list[int]:
    """Compute a MinHash signature for a set of shingles.

    Uses BLAKE2b with per-permutation personalisation bytes as a fast,
    independent hash family.

    :param shingles: List of shingle strings.
    :param num_perm: Number of hash permutations (signature length).
    :returns: List of *num_perm* integer values forming the MinHash signature.
    """
    signature = [2**63 - 1] * num_perm
    for shingle in shingles:
        encoded = shingle.encode("utf-8")
        for perm in range(num_perm):
            digest = hashlib.blake2b(
                encoded,
                digest_size=8,
                person=str(perm).encode().ljust(16, b"\x00")[:16],
            ).digest()
            value = int.from_bytes(digest, "big")
            if value < signature[perm]:
                signature[perm] = value
    return signature


def jaccard_from_signatures(sig1: list[int], sig2: list[int]) -> float:
    """Estimate the Jaccard similarity of two sets from their MinHash signatures.

    :param sig1: MinHash signature for the first set.
    :param sig2: MinHash signature for the second set.
    :returns: Estimated Jaccard similarity in [0.0, 1.0]; returns 0.0 if
        either signature is empty.
    """
    if not sig1 or not sig2:
        return 0.0
    matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
    return matches / len(sig1)


def cluster_near_duplicates(
    items: list[tuple[str, str]],
    ngram: int,
    num_perm: int,
    threshold: float,
) -> list[list[str]]:
    """Group documents into near-duplicate clusters using MinHash.

    Uses a greedy O(n²) clustering approach (sufficient for typical
    document-set sizes of hundreds to low thousands).

    :param items: List of ``(key, text)`` pairs where *key* is a document
        identifier (e.g. a file path) and *text* is the document content.
    :param ngram: Shingle size for token n-grams.
    :param num_perm: Number of MinHash permutations.
    :param threshold: Jaccard similarity threshold; document pairs above this
        value are placed in the same cluster.
    :returns: List of clusters, each cluster being a list of document keys.
        Every key appears in exactly one cluster.
    """
    signatures: dict[str, list[int]] = {
        key: minhash_signature(shingle_tokens(text, n=ngram), num_perm=num_perm)
        for key, text in items
    }
    keys = list(signatures)
    clusters: list[list[str]] = []
    seen: set[str] = set()

    for i, key_a in enumerate(keys):
        if key_a in seen:
            continue
        cluster = [key_a]
        seen.add(key_a)
        for key_b in keys[i + 1:]:
            if key_b in seen:
                continue
            if jaccard_from_signatures(signatures[key_a], signatures[key_b]) >= threshold:
                cluster.append(key_b)
                seen.add(key_b)
        clusters.append(cluster)

    return clusters
