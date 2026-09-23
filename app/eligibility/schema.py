from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


SCHEMA_VERSION = "eligibility-v1"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CriterionType(StrEnum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class RuleLogic(StrEnum):
    ALL = "all"
    ANY = "any"


class FactDomain(StrEnum):
    DEMOGRAPHIC = "demographic"
    DIAGNOSIS = "diagnosis"
    LAB = "lab"
    BIOMARKER = "biomarker"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    TREATMENT = "treatment"
    PERFORMANCE_STATUS = "performance_status"
    OTHER = "other"


class FactField(StrEnum):
    PRESENCE = "presence"
    VALUE = "value"
    DATE = "date"
    STATUS = "status"
    AGE_YEARS = "age_years"
    SEX_AT_BIRTH = "sex_at_birth"
    COUNT = "count"


class MappingStatus(StrEnum):
    SOURCE_PROVIDED = "source_provided"
    UNRESOLVED = "unresolved"


class ComparisonOperator(StrEnum):
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    BETWEEN = "between"


class TemporalRelation(StrEnum):
    WITHIN_DAYS_BEFORE = "within_days_before"
    WITHIN_DAYS_AFTER = "within_days_after"
    AT_LEAST_DAYS_BEFORE = "at_least_days_before"
    AT_LEAST_DAYS_AFTER = "at_least_days_after"
    BEFORE = "before"
    AFTER = "after"


class TemporalReference(StrEnum):
    SCREENING_DATE = "screening_date"
    ENROLMENT_DATE = "enrolment_date"
    CURRENT_DATE = "current_date"


Scalar = str | int | float | bool
ExpectedValue = Scalar | list[Scalar] | None


class FactReference(StrictModel):
    domain: FactDomain
    field: FactField
    concept_text: str = Field(min_length=1, max_length=500)
    code_system: str | None = Field(default=None, max_length=100)
    code: str | None = Field(default=None, max_length=200)
    mapping_status: MappingStatus = MappingStatus.UNRESOLVED

    @model_validator(mode="after")
    def validate_mapping(self) -> FactReference:
        if self.mapping_status == MappingStatus.SOURCE_PROVIDED:
            if not self.code_system or not self.code:
                raise ValueError("source_provided mappings require code_system and code")
        elif self.code_system is not None or self.code is not None:
            raise ValueError("unresolved mappings cannot contain terminology codes")
        return self


class TemporalConstraint(StrictModel):
    relation: TemporalRelation
    reference: TemporalReference
    days: int | None = Field(default=None, ge=0, le=36500)

    @model_validator(mode="after")
    def validate_days(self) -> TemporalConstraint:
        day_relations = {
            TemporalRelation.WITHIN_DAYS_BEFORE,
            TemporalRelation.WITHIN_DAYS_AFTER,
            TemporalRelation.AT_LEAST_DAYS_BEFORE,
            TemporalRelation.AT_LEAST_DAYS_AFTER,
        }
        if self.relation in day_relations and self.days is None:
            raise ValueError("days is required for day-based temporal rules")
        if self.relation not in day_relations and self.days is not None:
            raise ValueError("days must be omitted for simple before/after rules")
        return self


class RulePredicate(StrictModel):
    fact: FactReference
    operator: ComparisonOperator
    expected: ExpectedValue = None
    unit: str | None = Field(default=None, max_length=100)
    temporal: TemporalConstraint | None = None
    source_fragment: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_expected_value(self) -> RulePredicate:
        no_value_ops = {ComparisonOperator.EXISTS, ComparisonOperator.NOT_EXISTS}
        if self.operator in no_value_ops and self.expected is not None:
            raise ValueError("exists/not_exists predicates must not contain expected")
        if self.operator not in no_value_ops and self.expected is None:
            raise ValueError("comparison predicates require an expected value")
        if self.operator == ComparisonOperator.BETWEEN:
            if not isinstance(self.expected, list) or len(self.expected) != 2:
                raise ValueError("between requires exactly two expected values")
        return self


class CompiledCriterion(StrictModel):
    criterion_key: str = Field(pattern=r"^(INC|EXC)-[0-9]{3,}$")
    criterion_type: CriterionType
    source_text: str = Field(min_length=1, max_length=12000)
    logic: RuleLogic = RuleLogic.ALL
    predicates: list[RulePredicate] = Field(default_factory=list, max_length=30)
    automatable: bool
    needs_review: bool
    review_reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_execution_state(self) -> CompiledCriterion:
        expected_prefix = "INC-" if self.criterion_type == CriterionType.INCLUSION else "EXC-"
        if not self.criterion_key.startswith(expected_prefix):
            raise ValueError("criterion_key prefix must match criterion_type")
        if self.needs_review:
            if self.automatable:
                raise ValueError("a criterion requiring review cannot be automatable")
            if not self.review_reason:
                raise ValueError("review_reason is required when needs_review is true")
        if self.automatable and not self.predicates:
            raise ValueError("automatable criteria require at least one predicate")
        return self


class EligibilityCompilerOutput(StrictModel):
    criteria: list[CompiledCriterion] = Field(min_length=1, max_length=250)
    global_review_notes: list[str] = Field(default_factory=list, max_length=50)


class CompiledEligibilityRuleSet(StrictModel):
    schema_version: Literal["eligibility-v1"] = SCHEMA_VERSION
    source_id: str = Field(min_length=1, max_length=500)
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    rules_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    compiler_provider: Literal["openai"] = "openai"
    compiler_model: str = Field(min_length=1, max_length=200)
    compiler_response_id: str | None = Field(default=None, max_length=500)
    criteria: list[CompiledCriterion] = Field(min_length=1, max_length=250)
    global_review_notes: list[str] = Field(default_factory=list, max_length=50)


class CompileEligibilityRequest(StrictModel):
    source_id: str = Field(min_length=1, max_length=500)
    criteria_text: str = Field(min_length=1, max_length=60000)


class EligibilitySchemaResponse(StrictModel):
    schema_version: Literal["eligibility-v1"] = SCHEMA_VERSION
    json_schema: dict[str, Any]
