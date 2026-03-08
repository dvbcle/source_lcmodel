# Prompt Playbook

This playbook captures reusable prompt patterns from the full LCModel
Fortran-to-Python migration session.

Use this together with the full prompt archive:
`docs/archive/chat_transcript_full_2026-03-08.md`.

## Purpose

1. Help contributors learn prompt patterns that produced reliable engineering
   outcomes.
2. Preserve why specific prompting styles worked for parity, testing, and
   architecture migration tasks.
3. Tie prompts to objective evidence (tests, regression artifacts, and commit
   history).

## How To Use This Document

1. Pick a phase that matches your current task.
2. Reuse the prompt pattern and fill in your concrete file/routine details.
3. Keep validation requirements explicit in the prompt (unit tests, parity,
   external regression, docs updates).
4. Check linked commits and docs artifacts to see expected outcomes.

## Phase-Based Patterns

### 1. Initial Conversion And Bootstrap

- Goal: Establish a runnable Python baseline from Fortran sources.
- Example prompt:
  `Folder contains a set of fortran files. Please convert into a python program.`
- Why it worked:
  It set a clear top-level objective and enabled incremental follow-up prompts.
- Evidence:
  Early conversion scaffold commits beginning at `df9a857`.

### 2. Enforce Understandable Code And Atomic History

- Goal: Keep generated code maintainable and reviewable.
- Example prompt:
  `Add good comments to the code ... check in this version ... first commit ...`
- Why it worked:
  It required readability and disciplined commit checkpoints before deeper
  semantic changes.
- Evidence:
  Progressive commit history with focused scopes across conversion and refactor
  phases.

### 3. Drive Semantic Porting To Full Parity

- Goal: Replace placeholder behavior with algorithmic Python implementations.
- Example prompt:
  `Keep continuing until a full port is achieved.`
- Why it worked:
  It set a completion condition (full port) and avoided stopping at scaffold
  compatibility.
- Evidence:
  Porting sequence including solver, fitting, IO, and helper routines in commit
  history from `6175163` through `f992bdb` and beyond.

### 4. Require Hard Cutover To Python-First Runtime

- Goal: Move from migration compatibility layer to clean product surface.
- Example prompt:
  `Do the hard cutover while making sure no functionality is broken, via tests.`
- Why it worked:
  It coupled architectural cleanup with mandatory regression safety.
- Evidence:
  `010f01e` (runtime surface cutover) and related architecture commits.

### 5. Keep Traceability For Legacy Users

- Goal: Preserve routine-level mapping to original Fortran for audits/onboarding.
- Example prompt:
  `What other mechanism is there to maintain the traceability and routine level compatibility?`
- Why it worked:
  It prevented "rewrite drift" by requiring explicit provenance mechanisms.
- Evidence:
  `14dde07` plus docs:
  `docs/TRACEABILITY_SYSTEM.md`, `docs/FORTRAN_ROUTINE_MAP.md`.

### 6. Validate Against External Oracle Fixtures

- Goal: Confirm behavioral parity on independent reference data.
- Example prompt:
  `Proceed until the test of comparing out.ps with out_ref_build.ps is succesful`
- Why it worked:
  It specified a concrete pass/fail oracle comparison target.
- Evidence:
  `docs/EXTERNAL_REGRESSION_PROOF.md`, `6ea2ab7`, and subsequent updates.

### 7. Keep Documentation In Lockstep

- Goal: Ensure docs explain current architecture and contributor workflow.
- Example prompt:
  `Update the README files to better reflect current status ...`
- Why it worked:
  It treated docs as a release artifact, not a post-hoc task.
- Evidence:
  README/doc refinement commits such as `bf2a0ef`, `432a75d`, `5de0ea5`,
  `eb20f0b`.

### 8. Add Structured Performance Work

- Goal: Introduce measurable optimization with compatibility fallback.
- Example prompt:
  `Implement option 1, with a fallback of allowing non-numpy based execution ...`
- Why it worked:
  It constrained optimization by safety requirements and fallback behavior.
- Evidence:
  `f592c8c`, `c9cfe92`, and measurement documentation in
  `docs/PERFORMANCE_MEASUREMENTS.md`.

### 9. Enforce Repeatable Quality Gates

- Goal: Prevent regressions during aggressive refactors.
- Example prompt:
  `... run the unit tests and the external regression test periodically ...`
- Why it worked:
  It encoded recurring validation into the workflow, not just release-time
  checks.
- Evidence:
  README workflow and repeated regression documentation updates.

### 10. Capture Prompting As Teachable Project Knowledge

- Goal: Turn one long migration session into reusable contributor guidance.
- Example prompt:
  `How can I capture all the prompts that were used for this project in a way that helps teach others?`
- Why it worked:
  It converted process knowledge into versioned project documentation.
- Evidence:
  This playbook and archived prompt transcript.

## Prompting Guidelines Learned From This Project

1. State the desired end state explicitly (`full parity`, `hard cutover`,
   `no remaining blocks`).
2. Include verification expectations in the prompt (`run unit tests`,
   `external regression`, `parity audit`).
3. Ask for checkpointed commits when a change spans multiple risk areas.
4. Separate goals by phase (parity first, architecture/readability next,
   performance after baseline confidence).
5. Require documentation updates for user-visible or workflow-visible changes.

