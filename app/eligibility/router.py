from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.eligibility.compiler import (
    CompilerValidationError,
    OpenAIEligibilityCompiler,
    compiler_json_schema,
)
from app.eligibility.schema import (
    CompiledEligibilityRuleSet,
    CompileEligibilityRequest,
    EligibilitySchemaResponse,
    SCHEMA_VERSION,
)


router = APIRouter(prefix="/v1/eligibility", tags=["eligibility"])


@router.get("/schema", response_model=EligibilitySchemaResponse)
def get_eligibility_schema() -> EligibilitySchemaResponse:
    return EligibilitySchemaResponse(
        schema_version=SCHEMA_VERSION,
        json_schema=compiler_json_schema(),
    )


@router.post("/compile", response_model=CompiledEligibilityRuleSet)
def compile_eligibility(
    request: CompileEligibilityRequest,
) -> CompiledEligibilityRuleSet:
    settings = get_settings()
    if not settings.openai_configured:
        raise HTTPException(
            status_code=503,
            detail="OpenAI compiler is not configured",
        )

    try:
        return OpenAIEligibilityCompiler().compile(
            source_id=request.source_id,
            criteria_text=request.criteria_text,
        )
    except CompilerValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Eligibility compiler request failed",
        ) from exc
