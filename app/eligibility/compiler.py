from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache

from openai import OpenAI

from app.config import get_settings
from app.eligibility.schema import (
    SCHEMA_VERSION,
    CompiledEligibilityRuleSet,
    EligibilityCompilerOutput,
)


COMPILER_INSTRUCTIONS = """You are the Vector12 eligibility compiler.

Your only job is to translate clinical-trial eligibility criteria into the
provided machine-readable schema. You are NOT deciding whether any patient is
eligible.

Rules:
1. Preserve each criterion's source_text faithfully. Do not paraphrase it.
2. Assign inclusion criteria keys INC-001, INC-002, ... in source order and
   exclusion criteria keys EXC-001, EXC-002, ... in source order.
3. Never invent terminology codes. Only populate code_system/code when the
   source text itself explicitly supplies that code. Otherwise set both to null
   and mapping_status to unresolved.
4. If a criterion cannot be represented safely with the available operators,
   contains mixed/nested logic that cannot be flattened without changing its
   meaning, depends on clinician judgement, or is otherwise ambiguous, set
   automatable=false, needs_review=true, and explain why in review_reason.
5. Missing or ambiguous source information must never be guessed.
6. source_fragment must be an exact fragment from the criterion that supports
   that predicate.
7. Use units exactly as stated. Do not silently convert units.
8. Temporal language must be represented explicitly using temporal constraints.
9. Do not create patient facts, infer patient values, or produce an eligibility
   verdict.
10. A soft ranking score is not part of this schema. Trial inclusion/exclusion
    criteria remain explicit criteria.
"""


class CompilerValidationError(ValueError):
    pass


def _normalise_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compiler_json_schema() -> dict:
    return EligibilityCompilerOutput.model_json_schema()


@lru_cache
def get_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_configured:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key)


def finalise_compilation(
    *,
    source_id: str,
    criteria_text: str,
    output: EligibilityCompilerOutput,
    compiler_model: str,
    compiler_response_id: str | None = None,
) -> CompiledEligibilityRuleSet:
    normalised_source = _normalise_whitespace(criteria_text)

    for criterion in output.criteria:
        if _normalise_whitespace(criterion.source_text) not in normalised_source:
            raise CompilerValidationError(
                f"{criterion.criterion_key} source_text is not traceable "
                "to the supplied eligibility text"
            )
        for predicate in criterion.predicates:
            if (
                _normalise_whitespace(predicate.source_fragment)
                not in _normalise_whitespace(criterion.source_text)
            ):
                raise CompilerValidationError(
                    f"{criterion.criterion_key} contains a predicate whose "
                    "source_fragment is not traceable to source_text"
                )

    rules_material = {
        "schema_version": SCHEMA_VERSION,
        "criteria": [
            criterion.model_dump(mode="json")
            for criterion in output.criteria
        ],
        "global_review_notes": output.global_review_notes,
    }

    return CompiledEligibilityRuleSet(
        source_id=source_id,
        source_hash=_sha256_text(criteria_text),
        rules_hash=_sha256_text(_canonical_json(rules_material)),
        compiler_model=compiler_model,
        compiler_response_id=compiler_response_id,
        criteria=output.criteria,
        global_review_notes=output.global_review_notes,
    )


class OpenAIEligibilityCompiler:
    def __init__(
        self,
        *,
        client: OpenAI | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self.client = client or get_openai_client()
        self.model = model or settings.openai_model

    def compile(
        self,
        *,
        source_id: str,
        criteria_text: str,
    ) -> CompiledEligibilityRuleSet:
        response = self.client.responses.create(
            model=self.model,
            instructions=COMPILER_INSTRUCTIONS,
            input=criteria_text,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "vector12_eligibility_rules",
                    "description": (
                        "A strict machine-readable translation of clinical "
                        "trial eligibility criteria."
                    ),
                    "schema": compiler_json_schema(),
                    "strict": True,
                }
            },
        )

        if not response.output_text:
            raise CompilerValidationError(
                "OpenAI returned no structured eligibility output"
            )

        output = EligibilityCompilerOutput.model_validate_json(
            response.output_text
        )

        return finalise_compilation(
            source_id=source_id,
            criteria_text=criteria_text,
            output=output,
            compiler_model=self.model,
            compiler_response_id=getattr(response, "id", None),
        )
