import os
import sys
import hashlib
import re
from collections import Counter, defaultdict

import chromadb

BATCH = 100

client = chromadb.CloudClient(
    tenant=os.environ["CHROMA_TENANT"],
    database=os.environ.get("CHROMA_DATABASE", "policypal"),
    api_key=os.environ["CHROMA_API_KEY"],
)
col = client.get_collection("policypal")


def chunk_key(text):
    return hashlib.sha256(" ".join(text.split()).lower().encode()).hexdigest()


def load_all(page=250):
    offset = 0
    while True:
        res = col.get(include=["documents", "metadatas"], limit=page, offset=offset)
        if not res["ids"]:
            return
        yield from zip(res["ids"], res["documents"], res["metadatas"])
        offset += page


def audit():
    by_source, groups = Counter(), defaultdict(list)
    for id_, doc, meta in load_all():
        src = meta.get("source_name") or meta.get("source", "?")
        by_source[src] += 1
        groups[chunk_key(doc)].append(src)
    dupes = [v for v in groups.values() if len(v) > 1]
    total = sum(by_source.values())
    print("Chunks per source:", dict(by_source))
    print(f"Total chunks: {total}, unique texts: {len(groups)}")
    print(f"Duplicate groups: {len(dupes)}, extra copies: {total - len(groups)}")
    for v in dupes[:5]:
        print("  e.g. sources:", v)


def rank(name):
    n = name.lower()
    if n.startswith("tmp"):
        return 2
    if re.search(r"- copy|\(\d+\)", n):
        return 1
    return 0



def cleanup():
    groups = defaultdict(list)
    for id_, doc, meta in load_all():
        groups[chunk_key(doc)].append((id_, meta.get("source_name") or meta.get("source", "")))
    to_delete = []
    for items in groups.values():
        keep = min(items, key=lambda i: rank(i[1]))
        to_delete += [i[0] for i in items if i[0] != keep[0]]
    print(f"Will delete {len(to_delete)} duplicate chunks and keep {len(groups)} unique ones.")
    if input("Type yes to proceed: ").strip().lower() != "yes":
        print("Aborted.")
        return
    for i in range(0, len(to_delete), BATCH):
        col.delete(ids=to_delete[i:i + BATCH])
    print("Done.")
if __name__ == "__main__":
    audit() if (len(sys.argv) < 2 or sys.argv[1] == "audit") else cleanup()