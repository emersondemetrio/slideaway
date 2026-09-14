---
name: code-review
description: Domain-aware code review for this repo - FastAPI/Python backend, Svelte frontend, Kotlin/Android mobile, and general infra/config. Reviews a diff, branch, or PR against real, sourced best-practices references per domain, verifies every candidate finding against the actual code before reporting anything, and reports via the ReportFindings tool. Use when reviewing a PR, auditing a branch's changes, or checking code quality in this repo.
---

# Code Review

Reviews changed code in this repo against domain-specific, sourced references, then verifies every candidate before reporting it. The point of the verification pass is to eliminate hallucinated or unverifiable findings, not just to sound thorough - a finding this skill reports must be something a reviewer could open the file and confirm in under a minute.

## 1. Scope the review

Get the actual diff or file list for the target (a PR number, a branch compared to `main`, or specific files named by the user). Only review what actually changed, unless explicitly asked to audit the whole repo.

## 2. Route to the right reference(s) per changed file

- `apps/api/**/*.py` -> read `.claude/skills/fastapi-code-review/references/best-practices.md` (vendored, MIT-licensed, from mvilrokx/claude-skills) alongside general Python judgment.
- `apps/web/**/*.svelte`, `apps/web/**/*.js`, `apps/web/**/*.css` -> read `references/svelte.md`.
- `apps/mobile/android/**/*.kt` -> read `references/kotlin-android.md`.
- `docker-compose.yml`, `Dockerfile`, `pyproject.toml`, `package.json`, `.env.example` -> general infra/config judgment: hardcoded secrets, exposed ports that shouldn't be, dependency versions pinned inconsistently, anything that contradicts what's already decided in `DECISIONS.md`.

A single PR often touches more than one of these - apply every reference that matches a changed file, not just one.

## 3. Gather candidate findings

Read the actual changed code, not just the diff hunks in isolation - open the full file when a finding depends on context the diff alone doesn't show (e.g. whether a `Depends()` chain already handles something a diff line seems to be missing). For each potential issue, note: file, line, what the reference says the correct pattern is, and what the code actually does.

Do not flag:
- Style/formatting already enforced by `ruff`/lint config - that's the linter's job, not this skill's.
- Anything the reference itself lists as low-priority polish, unless there are several in the same area.
- A pattern that looks like a violation from the diff alone but is actually handled elsewhere in the same file/request (check before flagging).

## 4. Verify every candidate before reporting

This is the step that separates real findings from hallucinated ones. For each candidate:

1. Re-open the exact file and line cited. Confirm the code actually says what the finding claims.
2. Confirm the reference material actually supports the claim - quote or paraphrase the specific rule, don't invent one.
3. Ask: could this be explained by something the reviewer hasn't seen yet (a dependency defined elsewhere, an intentional tradeoff already logged in `DECISIONS.md`)? If so, either drop it or note the tension explicitly rather than asserting a defect.
4. Assign a confidence level. Only keep findings that are directly verifiable from code actually read in this pass - discard anything resting on assumption or memory rather than the file in front of you.

Never cite a file:line you have not opened and read during this review.

## 5. Report

Call `ReportFindings` once with the surviving findings, ranked most-severe first. Each finding should name the domain reference it came from (e.g. "per fastapi-code-review: N+1 query pattern") so the source of the standard is traceable, not just asserted.
