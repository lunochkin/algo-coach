"""One timed session on one problem: what the drill loop serves, judges and
mints."""

# the cap a sitting judges a submission under. The speedup search picks the
# separating size against it, and generation's own cap sits well above it
DRILL_CAP_MS = 2_000
