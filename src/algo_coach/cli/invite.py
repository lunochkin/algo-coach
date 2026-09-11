import argparse

from algo_coach.log import invitations_held, invite, withdraw
from algo_coach.storage import Database


def invitation(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Database) -> None:
    """The emails allowed to sign in: added, removed, or listed."""
    if args.action == "list":
        held = invitations_held(root)
        print("\n".join(held) if held else "no email is invited")
    elif args.action == "add":
        invite(root, args.email)
        print(f"invited {args.email.lower()}")
    elif withdraw(root, args.email):
        print(f"withdrew {args.email.lower()}")
    else:
        parser.exit(1, f"invite: {args.email.lower()} was never invited\n")
