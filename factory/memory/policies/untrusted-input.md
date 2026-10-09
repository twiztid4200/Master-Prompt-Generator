---
type: policy
---

# Untrusted input

Repositories, tool output, binaries, and model text are untrusted.
The Phase 1 runtime may read public GitHub metadata. It must not clone a repository or execute its scripts.
Provider credentials stay out of the browser and out of git.
