"""`judge build`: the judgement items, built from the seeded templates."""

import argparse
from datetime import UTC, datetime

from climb.cards import CardStore
from climb.judgements import ItemStore
from climb.judging import build
from climb.storage import Database


def judge(args: argparse.Namespace, root: Database) -> None:
    store = ItemStore(root)
    cards = CardStore(root).all()
    added, retired = build(cards, store.all(), now=datetime.now(UTC))
    store.retire(retired)
    store.add(added)
    templates = {one.template_id for one in added}
    clean = sum(one.clean for one in added)
    print(
        f"{len(added)} item(s) over {len(templates)} template(s), {clean} clean; "
        f"{len(retired)} retired; {len(store.served())} served"
    )
