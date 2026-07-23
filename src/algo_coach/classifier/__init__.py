"""Failure-mode classifier (Phase 1).

Takes one Attempt, returns a Diagnosis: mode in {speed, rust, gap, syntax,
none} + confidence + quoted evidence, via structured LLM output. Sampling
kept near-deterministic; model id and prompt version recorded on every
Diagnosis so eval numbers stay attributable.

Implementation lands in the `feat: llm failure classifier` slice.
"""
