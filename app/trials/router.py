from fastapi import APIRouter, HTTPException

from app.trials.clinicaltrials_gov import (
    ClinicalTrialsGovClient,
    ClinicalTrialsGovError,
)
from app.trials.schema import TrialImportResponse


router = APIRouter(prefix="/v1/trials", tags=["trials"])


@router.get(
    "/clinicaltrials-gov/{nct_id}",
    response_model=TrialImportResponse,
)
def import_clinicaltrials_gov_trial(
    nct_id: str,
) -> TrialImportResponse:
    try:
        trial = ClinicalTrialsGovClient().fetch_study(nct_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ClinicalTrialsGovError as exc:
        message = str(exc)
        status_code = 404 if "was not found" in message else 502
        raise HTTPException(status_code=status_code, detail=message) from exc

    return TrialImportResponse(trial=trial)
