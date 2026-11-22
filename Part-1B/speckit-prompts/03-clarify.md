Run /speckit.clarify and answer its questions yourself; record the answers. Be ready to settle:
1. A request whose time is already past today (e.g. "9am today" at 10:00): clarify, or schedule next occurrence? (Spec: either
   is acceptable; a past datetime never is.)
2. "in the evening": clarify or choose 17:00-21:00? (Spec: either; window 17:00-21:00 if created.)
3. Which date does "this coming Monday" mean when today is Saturday? (Spec: the next Monday.)
4. Hindi requests: reply language of clarification_question? (Spec: any; evaluated by keywords only for English cases.)
Do not use clarification to weaken an invariant, guardrail, or the threshold.
