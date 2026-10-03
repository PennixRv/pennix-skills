"""Pennix's thin same-process Cognee recall extension.

The official Cognee API remains the owner of auth, ACL, DTO validation, recall,
SSE framing, serialization, errors, and storage. This module only replaces the
POST recall route with the same handler contract while enabling the two
approved native retriever options and provenance metadata.
"""

from __future__ import annotations

import inspect

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse

from cognee import __version__ as COGNEE_VERSION
from cognee.api.client import app
from cognee.api.sse import SSE_MEDIA_TYPE, sse_headers, wants_event_stream
from cognee.api.v1.recall.recall import RecallResponse, recall as cognee_recall
from cognee.api.v1.recall.recall_stream import begin_recall_stream
from cognee.api.v1.recall.routers.get_recall_router import RecallPayloadDTO
from cognee.exceptions import CogneeApiError
from cognee.modules.users.methods import get_authenticated_user
from cognee.modules.users.models import User
from cognee.shared.logging_utils import get_logger
from cognee.shared.usage_logger import log_usage
from cognee.shared.utils import send_telemetry


EXPECTED_COGNEE_VERSION = "1.6.2"
RETRIEVER_SPECIFIC_CONFIG = {
    "include_global_context_index": True,
    "use_truth_weight": True,
    "include_external_metadata": True,
}


if COGNEE_VERSION != EXPECTED_COGNEE_VERSION:
    raise RuntimeError(
        f"Pennix Cognee ingress requires Cognee {EXPECTED_COGNEE_VERSION}, found {COGNEE_VERSION}"
    )
if "retriever_specific_config" not in inspect.signature(cognee_recall).parameters:
    raise RuntimeError("Cognee recall SDK no longer exposes retriever_specific_config")


class EnhancedRecallPayloadDTO(RecallPayloadDTO):
    """Official recall payload; enhancement switches are deployment-owned."""


router = APIRouter()


@router.post("", response_model=list[RecallResponse])
@log_usage(function_name="POST /v1/recall", log_type="api_endpoint")
async def enhanced_recall(
    payload: EnhancedRecallPayloadDTO,
    request: Request,
    user: User = Depends(get_authenticated_user),
):
    send_telemetry(
        "Recall API Endpoint Invoked",
        user,
        additional_properties={
            "endpoint": "POST /v1/recall",
            "pennix_enhancements": True,
            "cognee_version": COGNEE_VERSION,
        },
    )

    from cognee.modules.recall.methods.model_from_json_schema import model_from_json_schema

    response_model = (
        model_from_json_schema(payload.response_schema)
        if payload.response_schema is not None
        else None
    )

    def run_recall():
        return cognee_recall(
            query_text=payload.query,
            query_type=payload.search_type,
            user=user,
            datasets=payload.datasets,
            dataset_ids=payload.dataset_ids,
            system_prompt=payload.system_prompt,
            node_name=payload.node_name,
            top_k=payload.top_k,
            verbose=payload.verbose,
            only_context=payload.only_context,
            session_id=payload.session_id,
            scope=payload.scope,
            context_profile=payload.context_profile,
            include_references=payload.include_references,
            response_model=response_model,
            tool_connections=payload.tool_connections,
            tools_trigger=payload.tools_trigger,
            code_query=payload.code_query,
            retriever_specific_config=RETRIEVER_SPECIFIC_CONFIG,
        )

    streaming = wants_event_stream(request.headers.get("accept"), payload.stream)
    try:
        if streaming:
            started = await begin_recall_stream(run_recall)
            return StreamingResponse(
                started.frames(), media_type=SSE_MEDIA_TYPE, headers=sse_headers()
            )
        return jsonable_encoder(await run_recall())
    except CogneeApiError:
        raise
    except ValueError:
        from cognee.memory.entries import _VALID_SCOPES

        get_logger().warning("Enhanced recall request validation failed", exc_info=True)
        return JSONResponse(
            status_code=422,
            content={
                "error": "Invalid recall request. If a scope was given, valid values are: "
                f"{sorted(_VALID_SCOPES)}."
            },
        )
    except Exception:
        get_logger().exception("Enhanced recall endpoint error")
        return JSONResponse(status_code=409, content={"error": "An error occurred during recall."})


# The official app already owns /api/v1/recall. Replace only its POST route in
# memory, leaving GET history and every other official route untouched.
for route in list(app.router.routes):
    if getattr(route, "path", None) == "/api/v1/recall" and "POST" in getattr(route, "methods", set()):
        app.router.routes.remove(route)
app.include_router(router, prefix="/api/v1/recall", tags=["recall", "pennix"])
