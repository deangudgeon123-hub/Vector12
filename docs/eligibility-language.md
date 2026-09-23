# Vector12 Eligibility Language v1

Vector12 compiles trial eligibility prose into a constrained rule language before any patient matching takes place.

The compiler translates source language only. It does not decide whether a patient is eligible. A criterion is executable only when its meaning can be represented without guessing. Ambiguous, subjective, or unsupported criteria are marked for review and are not treated as executable.

Every compiled criterion retains its source text, and every predicate retains the exact source fragment that supports it. Compiler output is rejected when those strings cannot be traced back to the supplied eligibility text.

The model is not allowed to invent ICD-10, SNOMED CT, LOINC, RxNorm, or other terminology codes. A code may only be emitted when the source itself explicitly supplies that code. Otherwise the concept remains unresolved for a later terminology mapping or human-review step.

Version 1 supports a criterion containing either an all or any set of predicates. If preserving the meaning would require mixed or deeper nested logic, the criterion must be sent to review rather than flattened incorrectly.

Temporal requirements are represented separately from value comparisons. The schema supports day windows before or after screening or enrolment, plus simple before and after relationships.

A compiled rule set receives a hash of the source text, a hash of the canonical compiled rules, the schema version, the compiler model, and the provider response ID when available. These fields support later reproducibility and audit.
