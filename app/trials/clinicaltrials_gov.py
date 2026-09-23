from __future__ import annotations

import re

import httpx

from app.trials.schema import ImportedTrial


BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
NCT_PATTERN = re.compile(r"^NCT[0-9]{8}$")


class ClinicalTrialsGovError(RuntimeError):
    pass


def validate_nct_id(nct_id: str) -> str:
    normalized = nct_id.strip().upper()
    if not NCT_PATTERN.fullmatch(normalized):
        raise ValueError("NCT ID must match NCT followed by 8 digits")
    return normalized


def normalise_study(payload: dict) -> ImportedTrial:
    protocol = payload.get("protocolSection") or {}
    identification = protocol.get("identificationModule") or {}
    status = protocol.get("statusModule") or {}
    sponsor = protocol.get("sponsorCollaboratorsModule") or {}
    design = protocol.get("designModule") or {}
    eligibility = protocol.get("eligibilityModule") or {}

    nct_id = validate_nct_id(str(identification.get("nctId", "")))
    criteria = eligibility.get("eligibilityCriteria")
    if not isinstance(criteria, str) or not criteria.strip():
        raise ClinicalTrialsGovError(
            f"{nct_id} does not contain usable eligibility criteria"
        )

    lead_sponsor = sponsor.get("leadSponsor") or {}

    brief_title = identification.get("briefTitle")
    official_title = identification.get("officialTitle")
    title = brief_title or official_title or nct_id

    phases = design.get("phases") or []
    if isinstance(phases, str):
        phases = [phases]

    return ImportedTrial(
        external_id=nct_id,
        title=str(title),
        official_title=(
            str(official_title) if official_title is not None else None
        ),
        sponsor=(
            str(lead_sponsor.get("name"))
            if lead_sponsor.get("name") is not None
            else None
        ),
        phases=[str(value) for value in phases],
        recruitment_status=(
            str(status.get("overallStatus"))
            if status.get("overallStatus") is not None
            else None
        ),
        study_type=(
            str(design.get("studyType"))
            if design.get("studyType") is not None
            else None
        ),
        minimum_age=(
            str(eligibility.get("minimumAge"))
            if eligibility.get("minimumAge") is not None
            else None
        ),
        maximum_age=(
            str(eligibility.get("maximumAge"))
            if eligibility.get("maximumAge") is not None
            else None
        ),
        sex=(
            str(eligibility.get("sex"))
            if eligibility.get("sex") is not None
            else None
        ),
        eligibility_text=criteria.strip(),
        source_url=f"https://clinicaltrials.gov/study/{nct_id}",
    )


class ClinicalTrialsGovClient:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds

    def fetch_study(self, nct_id: str) -> ImportedTrial:
        nct_id = validate_nct_id(nct_id)
        url = f"{BASE_URL}/{nct_id}"

        owns_client = self._client is None
        client = self._client or httpx.Client(
            timeout=self._timeout_seconds,
            headers={
                "Accept": "application/json",
                "User-Agent": "Vector12/0.3",
            },
        )

        try:
            response = client.get(url)
        except httpx.HTTPError as exc:
            raise ClinicalTrialsGovError(
                "ClinicalTrials.gov request failed"
            ) from exc
        finally:
            if owns_client:
                client.close()

        if response.status_code == 404:
            raise ClinicalTrialsGovError(f"Trial {nct_id} was not found")
        if response.status_code >= 400:
            raise ClinicalTrialsGovError(
                f"ClinicalTrials.gov returned HTTP {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ClinicalTrialsGovError(
                "ClinicalTrials.gov returned invalid JSON"
            ) from exc

        return normalise_study(payload)
