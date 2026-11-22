Run /speckit.clarify with no extra instructions first and answer its questions yourself.
Questions you should be ready to settle explicitly (record your answers in the clarification section):
1. Should `done -> in_progress` be allowed? (Spec says no; confirm.)
2. Concurrent writers: confirm this is out of scope and last-writer-wins is acceptable.
3. Is tag filtering exact-match only (no prefix/substring)? (Spec: exact.)
4. Should the CLI accept `--tag` repeated, or comma-separated? (Spec: repeated.)
5. Are non-ASCII characters allowed in titles? (Spec: yes, any str of 1..100 chars; tags are ASCII only.)
Do not use clarification to change an acceptance criterion in a way that contradicts the locked tests.
