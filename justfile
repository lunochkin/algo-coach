# Command recipes. `just` runs them from this directory whatever the shell's
# own is, which the relative `data/` root depends on.
#
#     brew install just

# What is here.
default:
    @just --list --unsorted

# --- development ---

# Create or update the environment.
sync:
    uv sync

# Run the tests.
test *args:
    uv run pytest {{ args }}

# Lint.
lint *args:
    uv run ruff check {{ args }}

# Format.
fmt:
    uv run ruff format .

# Lint and test, as a commit does.
check: lint test

# Enable the pre-commit and commit-msg hooks. Once per clone.
hooks:
    git config core.hooksPath .githooks

# --- ingest ---

# Ingest pushed problems. Before the attempts naming them.
push-problems source *args:
    uv run algo-coach push problems {{ source }} {{ args }}

# Ingest pushed attempts.
push-attempts source *args:
    uv run algo-coach push attempts {{ source }} {{ args }}

# Seed authored cards into the store.
seed source="content/cards":
    uv run algo-coach seed cards {{ source }}

# --- practice ---

# Per-technique standing.
board *args:
    uv run algo-coach board {{ args }}

# Pick a technique, then a problem for it.
drill *args:
    uv run algo-coach drill {{ args }}

# --- attribution ---

# Claim stored attempts by hand: the eval set.
claim *args:
    uv run algo-coach claim {{ args }}

revise:
    uv run algo-coach claim --revise --disputed 1 --model anthropic/claude-opus-5 --effort medium --provider anthropic --temperature default

# Claim stored attempts with the classifier.
classify *args:
    uv run algo-coach classify {{ args }}

# The classifier against the user's own claims.
score *args:
    uv run algo-coach score --concurrency 4 \
        --model anthropic/claude-opus-5 --provider anthropic --temperature default \
        --model google/gemma-4-31b-it --provider coreweave/bf16 \
        --model openai/gpt-oss-120b --provider coreweave/fp4 \
        --model google/gemini-3.7-flash --provider google-ai-studio \
        --model google/gemini-3.1-pro-preview --provider google-ai-studio \
        --model openai/gpt-5.6-sol --provider openai --temperature default \
        --model openai/gpt-5.6-terra --provider openai --temperature default \
        --model openai/gpt-5.6-luna --provider openai --temperature default \
        --model z-ai/glm-5.2 --provider gmicloud/fp8  \
        {{ args }}

# How far the classifier's claims move the board off the tags.
movement *args:
    uv run algo-coach movement {{ args }}

# --- matching ---

# Which of a card's templates a problem exercises, by hand.
annotate *args:
    uv run algo-coach annotate {{ args }}

# Match the corpus against a card's templates.
match *args:
    uv run algo-coach match {{ args }}

# --- analysis ---

views:
    duckdb -ui views.duckdb

# Rebuild the SQL views over the logs.
views-rebuild:
    uv run --with duckdb python scripts/views.py
