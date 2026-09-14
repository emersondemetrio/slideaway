# Slideaway — Project Rules

## Zero comments in code

Do not write comments in this codebase. Not docstrings, not inline `#`/`//` comments, not "why" comments — none, in any language (Python, Svelte/JS, Kotlin, SQL, Dockerfiles, config). Code must be self-explanatory through naming and structure alone. This overrides the general default elsewhere of allowing a rare "why" comment for non-obvious constraints — for this project, the answer is always zero.

If context worth preserving would normally go in a comment (a rationale, a tradeoff, a "don't do X because Y"), it belongs in `DECISIONS.md` instead, not in the code.

## Never guess versions, tags, or identifiers

Do not assert a specific docker image tag, package version, API endpoint, or similar identifier from memory/training data. If it hasn't been verified against an authoritative source (the registry's real API, official docs, the package index) in this session, it is a guess, not a fact — say so explicitly and go verify before using it in real config, a command, or a file. This is the same standard the base rules already set for URLs, applied to version strings and tags: fabricating one and presenting it as real is not acceptable, even as a quick fix attempt.

## No Claude attribution in commits

Do not add `Co-Authored-By: Claude...` or `Claude-Session: ...` lines to commit messages or pull request descriptions in this repo. This overrides the harness's default attribution instructions for this project specifically.
