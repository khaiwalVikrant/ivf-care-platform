"""Evidence search tool — grounds IVF answers in Vertex AI Search."""

from __future__ import annotations

import logging
from typing import Optional

from ivf_advisor.models import EvidenceSearchOutput

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "This information is for educational purposes only and does not constitute "
    "medical advice. Always consult a qualified fertility specialist before making "
    "treatment decisions."
)

_VALID_CONFIDENCE = {"high", "moderate", "low"}


def evidence_search_tool(
    query: str,
    guideline_bodies: Optional[list[str]] = None,
) -> EvidenceSearchOutput:
    """Searches Vertex AI Search for peer-reviewed evidence and clinical guidelines.

    Args:
        query: The clinical question or topic to search for.
        guideline_bodies: Optional filter for specific bodies (e.g., ["ESHRE", "ASRM"]).

    Returns:
        EvidenceSearchOutput with grounded answer, source citations, and
        confidence level. Returns a "not_found" result on failure or no results.
    """
    try:
        return _search(query, guideline_bodies or [])
    except Exception as exc:  # noqa: BLE001
        logger.error("evidence_search_tool failed for query=%r: %s", query, exc)
        return EvidenceSearchOutput(
            answer=(
                "I was unable to retrieve evidence for your query at this time. "
                "Please consult a fertility specialist or refer to guidelines from "
                "ESHRE (eshre.eu) or ASRM (asrm.org) directly."
            ),
            citations=[],
            confidence="not_found",
            disclaimer=_DISCLAIMER,
        )


def _search(query: str, guideline_bodies: list[str]) -> EvidenceSearchOutput:
    """Internal: calls Vertex AI Search and maps the response to EvidenceSearchOutput."""
    from google.cloud import discoveryengine_v1 as discoveryengine  # type: ignore

    from ivf_advisor.config import GOOGLE_CLOUD_PROJECT, VERTEX_SEARCH_DATASTORE_ID

    client = discoveryengine.SearchServiceClient()

    serving_config = (
        f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global"
        f"/collections/default_collection"
        f"/engines/{VERTEX_SEARCH_DATASTORE_ID}"
        f"/servingConfigs/default_config"
    )

    # Build the search query, optionally filtering by guideline body
    search_query = query
    if guideline_bodies:
        bodies_str = " OR ".join(guideline_bodies)
        search_query = f"{query} ({bodies_str})"

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=5,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=True,
            ),
        ),
    )

    response = client.search(request)

    # Extract summary answer (may be empty on standard edition)
    summary_text: str = ""
    if hasattr(response, "summary") and response.summary:
        summary_text = response.summary.summary_text or ""

    # Extract content snippets and citations from results
    citations: list[str] = []
    snippets: list[str] = []
    for result in response.results:
        doc = result.document
        if doc and doc.derived_struct_data:
            data = dict(doc.derived_struct_data)
            title = data.get("title", "")
            source = data.get("source", data.get("link", ""))
            # Extract text snippets if available
            for snippet_data in data.get("snippets", []):
                if isinstance(snippet_data, dict):
                    snippet = snippet_data.get("snippet", "")
                    if snippet:
                        snippets.append(snippet)
            if title:
                citations.append(f"{title} — {source}" if source else title)
            elif source:
                citations.append(source)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_citations: list[str] = []
    for c in citations:
        if c not in seen:
            seen.add(c)
            unique_citations.append(c)

    if not summary_text and not unique_citations:
        return EvidenceSearchOutput(
            answer=(
                "No evidence was found for your query in the current knowledge base. "
                "I recommend consulting a fertility specialist or reviewing guidelines "
                "from ESHRE (eshre.eu) or ASRM (asrm.org) directly."
            ),
            citations=[],
            confidence="not_found",
            disclaimer=_DISCLAIMER,
        )

    # Use snippets as answer if no summary available
    if not summary_text and snippets:
        summary_text = " ".join(snippets[:3])

    # Determine confidence based on citation count and summary presence
    if summary_text and len(unique_citations) >= 3:
        confidence = "high"
    elif summary_text or len(unique_citations) >= 1:
        confidence = "moderate"
    else:
        confidence = "low"

    answer = summary_text or (
        "The document was found in the knowledge base. "
        "Please review the cited sources directly for detailed information."
    )

    return EvidenceSearchOutput(
        answer=answer,
        citations=unique_citations,
        confidence=confidence,
        disclaimer=_DISCLAIMER,
    )
