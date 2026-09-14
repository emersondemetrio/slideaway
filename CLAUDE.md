# Slideaway — Project Rules

## Zero comments in code

Do not write comments in this codebase. Not docstrings, not inline `#`/`//` comments, not "why" comments — none, in any language (Python, Svelte/JS, Kotlin, SQL, Dockerfiles, config). Code must be self-explanatory through naming and structure alone. This overrides the general default elsewhere of allowing a rare "why" comment for non-obvious constraints — for this project, the answer is always zero.

If context worth preserving would normally go in a comment (a rationale, a tradeoff, a "don't do X because Y"), it belongs in `DECISIONS.md` instead, not in the code.
