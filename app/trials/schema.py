from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportedTrial(StrictModel):
    external_id: str = Field(pattern=r"^NCT[0-9]{8}$")
    title: str
    official_title: str | None = None
    sponsor: str | None = None
    phases: list[str] = Field(default_factory=list)
    recruitment_status: str | None = None
    study_type: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    sex: str | None = None
    eligibility_text: str
    source_url: str
    source: str = "clinicaltrials.gov"


class TrialImportResponse(StrictModel):
    trial: ImportedTrial
