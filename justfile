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

# Run the tests, the integration tests on the Postgres TEST_DATABASE_URL names.
test *args:
    uv run pytest {{ args }}

# Run the unit tests alone: no database.
test-unit *args:
    uv run pytest -m "not integration" {{ args }}

# Lint.
lint *args:
    uv run ruff check {{ args }}

# Type-check the engine.
typecheck:
    uv run pyright

# A name nothing in src or tests references.
dead:
    uv run vulture

# Type-check and lint the frontend; a warning fails it.
web-check:
    cd web && npm run --silent typecheck
    cd web && npm run --silent lint

# Rewrite the schema snapshots after an intended tightening; the test holds them otherwise.
schemas:
    SCHEMA_SNAPSHOT=write uv run pytest -q -n 0 tests/test_schema_additive.py

# The tests with coverage, gated at `fail_under`. What CI runs in place of `test`.
coverage *args:
    uv run pytest --cov {{ args }}

# Mutate the engine and see which tests notice. Slow: hours, not seconds.
mutate *args:
    uv run --with mutmut mutmut run {{ args }}

# Format.
fmt:
    uv run ruff format .

# Lint, type-check, dead-code check and test, as a commit does, and the
# frontend's own type check and lint.
check: lint typecheck dead web-check test

# What CI runs: `check` with the unit tests alone, since CI has no Postgres
# yet. Coverage is gated over the whole suite, by `just coverage`.
ci: lint typecheck dead web-check test-unit

# Enable the pre-commit and commit-msg hooks. Once per clone.
hooks:
    git config core.hooksPath .githooks

# --- content ---

# Seed authored cards into the store.
seed source="content/cards":
    uv run algo-coach seed cards {{ source }}

# --- practice ---

# The drill loop: the API and the Vite dev server together, the dev server
# proxying `/api`. Ctrl+C stops both.
app:
    #!/usr/bin/env bash
    set -euo pipefail
    [ -d web/node_modules ] || npm --prefix web install
    # the API on any exit, so none is left holding the port the proxy names
    trap 'kill $(jobs -p) 2>/dev/null; wait' EXIT
    uv run python -m algo_coach.api --reload &
    npm --prefix web run dev

# Regenerate the page's API types from the app's OpenAPI schema, after a route
# or a response model changes.
types:
    uv run python -m algo_coach.api --openapi > web/src/api/openapi.json
    cd web && npx openapi-typescript src/api/openapi.json -o src/api/schema.d.ts

# Apply every migration the database named by DATABASE_URL has not had.
migrate:
    uv run alembic upgrade head

# Generate a migration from what the declared tables add, to be read before it
# is committed. A new enum type or value is written by hand.
migration name:
    uv run alembic revision --autogenerate -m "{{ name }}"

# Per-technique progress.
board *args:
    uv run algo-coach board {{ args }}

# --- attribution ---

# Claim stored attempts with the classifier.
claim-attempts *args:
    uv run algo-coach claim attempts {{ args }}

# Claim stored attempts by hand: the eval set.
claim-attempts-by-hand *args:
    uv run algo-coach claim attempts --by-hand {{ args }}

# Claim the stored canonicals with the classifier.
claim-solutions *args:
    uv run algo-coach claim solutions {{ args }}

revise:
    uv run algo-coach claim attempts --by-hand --revise --disputed 1 --model anthropic/claude-opus-5 --effort medium --provider anthropic --temperature default

adjudicate:
    uv run algo-coach score --concurrency 4 --model anthropic/claude-opus-5 --provider anthropic --temperature default

# The classifier against the user's own claims.
score *args:
    uv run algo-coach score --concurrency 4 \
        --model anthropic/claude-opus-5 --provider anthropic --temperature default \
        --model google/gemini-3.7-flash --provider google-ai-studio \
        --model openai/gpt-oss-120b --provider coreweave/fp4 \
        --model google/gemma-4-31b-it --provider coreweave/fp4 \
        --model nex-agi/nex-n2-mini --provider nex-agi \
        --model z-ai/glm-5.1 --provider baidu/fp8 \
        {{ args }}

# The classifier against the user's own claims.
score-stored *args:
    uv run algo-coach score --stored \
        --model anthropic/claude-fable-5             --provider anthropic --temperature default \
        --model anthropic/claude-opus-5              --provider anthropic --temperature default \
        --model anthropic/claude-sonnet-5            --provider anthropic --temperature default \
        --model arcee-ai/trinity-large-thinking      --provider parasail/fp4 \
        --model bytedance-seed/seed-1.6-flash        --provider seed/fp8 \
        --model bytedance-seed/seed-2.0-mini         --provider seed/fp8 \
        --model deepseek/deepseek-v3.2               --provider streamlake/fp8 \
        --model deepseek/deepseek-v4-flash           --provider baidu/fp8 \
        --model deepseek/deepseek-v4-pro-0813        --provider alibaba \
        --model google/gemini-2.5-flash              --provider google-ai-studio \
        --model google/gemini-2.5-flash-lite         --provider google-vertex/eu \
        --model google/gemini-3.1-flash-lite-preview --provider google-ai-studio \
        --model google/gemini-3.1-pro-preview        --provider google-ai-studio \
        --model google/gemini-3.7-flash              --provider google-ai-studio \
        --model google/gemma-4-26b-a4b-it            --provider deepinfra/fp8 \
        --model google/gemma-4-31b-it                --provider coreweave/fp4 \
        --model inception/mercury-2                  --provider inception \
        --model meta/muse-glimmer-30b                --provider deepinfra/bf16 \
        --model meta/muse-spark-1.2                  --provider meta \
        --model minimax/minimax-m2.7                 --provider mara \
        --model minimax/minimax-m3                   --provider coreweave/fp4 \
        --model mistralai/mistral-small-2603         --provider venice/fp8 \
        --model moonshotai/kimi-k2-thinking          --provider novita/bf16 \
        --model nex-agi/nex-n2-mini                  --provider nex-agi \
        --model nvidia/nemotron-3-nano-30b-a3b       --provider nebius/fp8 \
        --model nvidia/nemotron-3-super-120b-a12b    --provider digitalocean \
        --model nvidia/nemotron-3.5-lightning        --provider deepinfra/bf16 \
        --model openai/gpt-5-nano                    --provider openai --temperature default \
        --model openai/gpt-5.4-nano                  --provider openai --temperature default \
        --model openai/gpt-5.6-luna                  --provider openai --temperature default \
        --model openai/gpt-5.6-sol                   --provider openai --temperature default \
        --model openai/gpt-5.6-terra                 --provider openai --temperature default \
        --model openai/gpt-oss-120b                  --provider coreweave/fp4 \
        --model openai/gpt-oss-20b                   --provider coreweave/fp4 \
        --model qwen/qwen3-14b                       --provider deepinfra/fp8 \
        --model qwen/qwen3-32b                       --provider deepinfra/fp8 \
        --model qwen/qwen3-next-80b-a3b-thinking     --provider nebius/fp8 \
        --model qwen/qwen3.5-35b-a3b                 --provider parasail/fp8 \
        --model qwen/qwen3.8-27b                     --provider coreweave/fp8 \
        --model qwen/qwen3.8-max                     --provider alibaba \
        --model qwen3-30b-a3b-instruct-2507          --provider streamlake --effort default \
        --model stepfun/step-3.7-flash               --provider stepfun/fp8 \
        --model tencent/hy3                          --provider baidu/fp8 \
        --model upstage/solar-pro4                   --provider upstage \
        --model x-ai/grok-4.6                        --provider xai/zdr \
        --model xiaomi/mimo-v2.5                     --provider parasail/fp8 \
        --model xiaomi/mimo-v2.5-pro                 --provider digitalocean \
        --model z-ai/glm-4.6                         --provider venice/fp4 \
        --model z-ai/glm-4.7-flash                   --provider cloudflare \
        --model z-ai/glm-5.1                         --provider baidu/fp8 \
        --model z-ai/glm-5.2                         --provider gmicloud/fp8 \
        {{ args }}

# How far the classifier's claims move the board off the fallback.
movement *args:
    uv run algo-coach movement {{ args }}

# --- matching ---

# Which of a card's templates a problem exercises, by hand.
match-by-hand *args:
    uv run algo-coach match --by-hand {{ args }}

# Match the corpus against a card's templates.
match *args:
    uv run algo-coach match {{ args }}

# --- analysis ---

views:
    duckdb -ui views.duckdb

# Rebuild the SQL views over the logs.
views-rebuild:
    uv run --with duckdb python scripts/views.py
