import uuid


# Opaque and unguessable: nothing derives an id from a record's content, or two
# engines would mint the same id for different records.
def new_id() -> str:
    return uuid.uuid4().hex


__all__ = ["new_id"]
