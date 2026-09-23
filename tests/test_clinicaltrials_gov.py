import httpx
import pytest

from app.trials.clinicaltrials_gov import (
    ClinicalTrialsGovClient,
    ClinicalTrialsGovError,
    normalise_study,
    validate_nct_id,
)


SAMPLE_STUDY = {
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT12345678",
            "briefTitle": "Example Oncology Trial",
            "officialTitle": "A Phase II Example Oncology Trial",
        },
        "statusModule": {
            "overallStatus": "RECRUITING",
        },
        "sponsorCollaboratorsModule": {
            "leadSponsor": {
                "name": "Example Sponsor",
            }
        },
        "designModule": {
            "studyType": "INTERVENTIONAL",
            "phases": ["PHASE2"],
        },
        "eligibilityModule": {
            "minimumAge": "18 Years",
            "maximumAge": "80 Years",
            "sex": "ALL",
            "eligibilityCriteria": (
                "Inclusion Criteria:\n"
                "* Participants must be 18 years of age or older.\n"
                "Exclusion Criteria:\n"
                "* Prior treatment within 21 days."
            ),
        },
    }
}


def test_validate_nct_id_normalises_case() -> None:
    assert validate_nct_id("nct12345678") == "NCT12345678"


def test_validate_nct_id_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        validate_nct_id("NCT123")


def test_normalise_study_extracts_expected_fields() -> None:
    trial = normalise_study(SAMPLE_STUDY)

    assert trial.external_id == "NCT12345678"
    assert trial.title == "Example Oncology Trial"
    assert trial.sponsor == "Example Sponsor"
    assert trial.phases == ["PHASE2"]
    assert trial.recruitment_status == "RECRUITING"
    assert "Prior treatment within 21 days." in trial.eligibility_text


def test_fetch_study_handles_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not found"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    importer = ClinicalTrialsGovClient(client=client)

    with pytest.raises(ClinicalTrialsGovError, match="was not found"):
        importer.fetch_study("NCT12345678")

    client.close()


def test_fetch_study_uses_api_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/NCT12345678")
        return httpx.Response(200, json=SAMPLE_STUDY)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    importer = ClinicalTrialsGovClient(client=client)

    trial = importer.fetch_study("NCT12345678")

    assert trial.external_id == "NCT12345678"
    assert trial.study_type == "INTERVENTIONAL"

    client.close()
