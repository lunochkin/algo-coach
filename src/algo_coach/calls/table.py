from sqlalchemy import CheckConstraint, Column, Double, Integer, Table, Text

from algo_coach.storage import appended_column, metadata, timestamp

calls = Table(
    "calls",
    metadata,
    Column("id", Text, primary_key=True),
    appended_column(),
    Column("created_at", timestamp(), nullable=False),
    Column("model", Text, nullable=False),
    Column("effort", Text, nullable=False),
    Column("prompt", Text, nullable=False),
    Column("prompt_hash", Text, nullable=False),
    Column("response", Text),
    Column("error", Text),
    Column("reasoning", Text),
    Column("stop_reason", Text),
    Column("temperature", Double[float]()),
    Column("pin", Text),
    Column("provider", Text),
    Column("input_tokens", Integer),
    Column("output_tokens", Integer),
    Column("reasoning_tokens", Integer),
    Column("cost", Double[float]()),
    Column("elapsed_ms", Integer),
    Column("requests", Integer),
    Column("request_ms", Integer),
    # the record's own rules, held where a writer skipping the model meets them
    CheckConstraint("(response IS NULL) <> (error IS NULL)", name="answered_or_failed"),
    CheckConstraint("prompt <> '' AND prompt_hash <> ''", name="prompt_named"),
)
