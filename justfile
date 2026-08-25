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

# --- content ---

# Seed authored cards into the store.
seed source="content/cards":
    uv run algo-coach seed cards {{ source }}

# --- practice ---

# Per-technique standing.
board *args:
    uv run algo-coach board {{ args }}

# --- attribution ---

# Claim stored attempts by hand: the eval set.
claim *args:
    uv run algo-coach claim {{ args }}

revise:
    uv run algo-coach claim --revise --disputed 1 --model anthropic/claude-opus-5 --effort medium --provider anthropic --temperature default

# Claim stored attempts with the classifier.
classify *args:
    uv run algo-coach classify {{ args }}

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
