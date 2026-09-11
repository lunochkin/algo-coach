import argparse

from algo_coach.log import erased, whole_log
from algo_coach.storage import Database


def user_log(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Database) -> None:
    """One user's whole log: printed as JSON, or erased once the user id is
    typed back."""
    if args.action == "export":
        print(whole_log(root, args.user).model_dump_json(indent=2))
        return
    # typed back rather than a flag: the erasure cannot be undone, and a flag
    # carries over from a shell's history
    typed = input(f"every record of {args.user}'s log is erased; type {args.user} to confirm: ")
    if typed.strip() != args.user:
        parser.exit(1, "log: nothing erased\n")
    counted = erased(root, args.user)
    print("erased " + ", ".join(f"{count} {table}" for table, count in counted.items()))
