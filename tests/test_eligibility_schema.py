import pytest
from pydantic import ValidationError

from app.eligibility.compiler import CompilerValidationError, finalise_compilation
from app.eligibility.schema import (
    CompiledCriterion,
    ComparisonOperator,
    CriterionType,
    EligibilityCompilerOutput,
    FactDomain,
    FactField,
    FactReference,
    MappingStatus,
    RulePredicate,
)


def test_traceable_rule_set_hashes_are_created() -> None:
    source = "Inclusion: Participants must be 18 years of age or older."
    predicate = RulePredicate(
        fact=FactReference(
            domain=FactDomain.DEMOGRAPHIC,
            field=FactField.AGE_YEARS,
            concept_text="Age",
            mapping_status=MappingStatus.UNRESOLVED,
        ),
        operator=ComparisonOperator.GTE,
        expected=18,
        source_fragment="18 years of age or older",
    )
    output = EligibilityCompilerOutput(
        criteria=[
            CompiledCriterion(
                criterion_key="INC-001",
                criterion_type=CriterionType.INCLUSION,
                source_text="Participants must be 18 years of age or older.",
                predicates=[predicate],
                automatable=True,
                needs_review=False,
            )
        ]
    )
    result = finalise_compilation(
        source_id="fixture-1",
        criteria_text=source,
        output=output,
        compiler_model="test-model",
    )
    assert result.schema_version == "eligibility-v1"
    assert len(result.source_hash) == 64
    assert len(result.rules_hash) == 64


def test_untraceable_source_text_is_rejected() -> None:
    output = EligibilityCompilerOutput(
        criteria=[
            CompiledCriterion(
                criterion_key="INC-001",
                criterion_type=CriterionType.INCLUSION,
                source_text="A different source statement.",
                predicates=[],
                automatable=False,
                needs_review=True,
                review_reason="Fixture",
            )
        ]
    )
    with pytest.raises(CompilerValidationError):
        finalise_compilation(
            source_id="fixture-2",
            criteria_text="Participants must be adults.",
            output=output,
            compiler_model="test-model",
        )


def test_unresolved_mapping_cannot_contain_code() -> None:
    with pytest.raises(ValidationError):
        FactReference(
            domain=FactDomain.DIAGNOSIS,
            field=FactField.PRESENCE,
            concept_text="example condition",
            code_system="example-system",
            code="example-code",
            mapping_status=MappingStatus.UNRESOLVED,
        )
