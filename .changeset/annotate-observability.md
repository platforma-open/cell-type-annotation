---
'@platforma-open/milaboratories.cell-type-annotation.software': patch
---

Make annotation failures diagnosable.

A failing run reported only `Exited with code -1` with no output at all. The runner collects the
last log lines from the redirected stdout/stderr file, but Python block-buffers stdout when it is
not a tty, so a SIGKILL (an OOM kill, for instance) discards the buffer and every failure surfaces
as "no output was saved to logs" — with no indication of which step died.

- `log_message` writes to stderr, not stdout. The runner tails one file and prefers stderr over
  stdout (`collectLastLogLines`: StdErr -> StdLog -> StdOut), so anything logged to stdout never
  appears in the error report at all.
- entrypoint runs `python -u`, and `log_message` passes `flush=True`, so each line reaches the log
  file as it is emitted.
- every log line now carries peak RSS, and the loader logs the row count it actually read plus
  milestones around the gene-symbol join, the cell-identifier build and the sparse-matrix
  construction. A killed run now leaves a memory trajectory and a last-reached step.
