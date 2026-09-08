from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from pymilvus import DataType, FieldSchema, MilvusClient

from src.core.config import settings
from src.core.database import get_milvus_client
from src.core.llm import get_embedding
from src.models.campaign_state import GroundingCitation, UserInputState

logger = logging.getLogger(__name__)

COLLECTION_NAME = getattr(settings, "MILVUS_COLLECTION_NAME", "campaign_knowledge") or "campaign_knowledge"
EMBEDDING_DIM = 1536  # Default OpenAI text-embedding-3-small dimension


def ensure_collection(dim: int = EMBEDDING_DIM) -> MilvusClient:
    """Idempotently initialize Milvus collection with index and scalar fields."""
    client = get_milvus_client()
    try:
        if not client.has_collection(COLLECTION_NAME):
            schema = client.create_schema(
                auto_id=True,
                enable_dynamic_field=True,
                description="Campaign context, proof points, and RAG knowledge store",
            )
            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="campaign_id", datatype=DataType.VARCHAR, max_length=64)
            schema.add_field(field_name="category", datatype=DataType.VARCHAR, max_length=64)
            schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=512)
            schema.add_field(field_name="chunk_text", datatype=DataType.VARCHAR, max_length=4096)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dim)

            index_params = client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="AUTOINDEX",
                metric_type="COSINE",
            )
            index_params.add_index(
                field_name="campaign_id",
                index_type="INVERTED",
            )

            client.create_collection(
                collection_name=COLLECTION_NAME,
                schema=schema,
                index_params=index_params,
            )
            logger.info(f"Created Milvus collection '{COLLECTION_NAME}' with dim={dim}")
        return client
    except Exception as e:
        logger.error(f"Milvus collection initialization error: {e}")
        return client


def clean_content(raw: str) -> str:
    """Noise reduction: strips HTML tags, script/style, excessive whitespace."""
    if not raw:
        return ""
    # Remove HTML tags & scripts
    text = re.sub(r"<script[^>]*>([\S\s]*?)</script>", " ", raw, flags=re.IGNORECASE)
    text = re.sub(r"<style[^>]*>([\S\s]*?)</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove excessive blank lines and spaces
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_content(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """Deterministic token/character chunk boundary with controlled overlap."""
    cleaned = clean_content(text)
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        if end >= len(cleaned):
            chunks.append(cleaned[start:].strip())
            break

        # Find nearest boundary (newline, period, or space)
        split_pos = -1
        for delim in ["\n\n", "\n", ". ", " "]:
            pos = cleaned.rfind(delim, start + overlap, end)
            if pos != -1:
                split_pos = pos + len(delim)
                break

        if split_pos == -1 or split_pos <= start:
            split_pos = end

        chunk = cleaned[start:split_pos].strip()
        if chunk:
            chunks.append(chunk)

        start = max(start + 1, split_pos - overlap)

    return chunks


async def fetch_asset_text(asset: str) -> tuple[str, str]:
    """Fetch URL contents or return raw text with source attribution."""
    asset_str = asset.strip()
    if asset_str.startswith("http://") or asset_str.startswith("https://"):
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                res = await client.get(asset_str)
                if res.status_code == 200:
                    return clean_content(res.text), asset_str
                logger.warning(f"Failed to fetch {asset_str}: HTTP {res.status_code}")
                return "", asset_str
        except Exception as e:
            logger.warning(f"Network error fetching {asset_str}: {e}")
            return "", asset_str
    # Direct text/note
    return clean_content(asset_str), "inline_asset"


async def ingest_campaign_knowledge(campaign_id: str, user_input: UserInputState) -> int:
    """Extract, clean, chunk, vectorize, and store campaign knowledge in Milvus."""
    try:
        client = ensure_collection()
    except Exception as e:
        logger.error(f"Cannot connect to Milvus: {e}")
        return 0

    items_to_process: list[tuple[str, str, str]] = []  # (text, category, source)

    # 1. Base Product/Company Proposition
    base_text = (
        f"Company: {user_input.company_name}\n"
        f"Product/Service: {user_input.product_service}\n"
        f"Value Proposition: {user_input.value_proposition}\n"
        f"Target ICP: {user_input.target_icp}\n"
        f"Pricing Tier: {user_input.pricing_tier}\n"
        f"Target Geography: {user_input.target_geography}"
    )
    items_to_process.append((base_text, "base_proposition", "campaign_meta"))

    # 2. Case Studies & Proof Points
    for idx, cs in enumerate(user_input.case_studies):
        if cs.strip():
            items_to_process.append((cs.strip(), "proof_point", f"case_study_{idx+1}"))

    # 3. Competitive Differentiators
    for idx, diff in enumerate(user_input.differentiators):
        if diff.strip():
            items_to_process.append((diff.strip(), "battlecard", f"differentiator_{idx+1}"))

    # 4. Past Winning Copy
    for idx, copy in enumerate(user_input.past_winning_copy):
        if copy.strip():
            items_to_process.append((copy.strip(), "few_shot_style", f"winning_sample_{idx+1}"))

    # 5. External Content Assets / URLs
    for asset in user_input.content_assets:
        text, source = await fetch_asset_text(asset)
        if text:
            items_to_process.append((text, "product_doc", source))

    # 6. Dynamic Live Web Intelligence (Zero-Key DuckDuckGo)
    try:
        from src.services.web_search import perform_market_research
        web_intel = await perform_market_research(
            company_name=user_input.company_name,
            product_service=user_input.product_service,
            target_icp=user_input.target_icp,
            competitors=user_input.competitors,
        )
        for idx, item in enumerate(web_intel):
            snippet = item.get("snippet", "")
            source_url = item.get("url") or f"web_search_{idx+1}"
            if snippet:
                items_to_process.append((snippet, "web_intel", source_url))
        logger.info(f"Retrieved {len(web_intel)} dynamic web search items for Milvus ingestion")
    except Exception as search_err:
        logger.warning(f"Dynamic web research skipped due to: {search_err}")

    # Chunk and Vectorize
    rows_to_insert: list[dict[str, Any]] = []
    for raw_text, category, source in items_to_process:
        chunks = chunk_content(raw_text)
        for chunk in chunks:
            if not chunk or len(chunk) < 5:
                continue
            try:
                embedding = await get_embedding(chunk)
                rows_to_insert.append({
                    "campaign_id": campaign_id,
                    "category": category,
                    "source": source[:512],
                    "chunk_text": chunk[:4096],
                    "vector": embedding,
                })
            except Exception as emb_err:
                logger.warning(f"Failed to generate embedding for chunk: {emb_err}")

    if rows_to_insert:
        try:
            client.insert(collection_name=COLLECTION_NAME, data=rows_to_insert)
            logger.info(f"Ingested {len(rows_to_insert)} chunks for campaign {campaign_id} into Milvus")
            return len(rows_to_insert)
        except Exception as insert_err:
            logger.error(f"Failed to insert chunks into Milvus: {insert_err}")
            return 0
    return 0


async def search_campaign_knowledge(
    campaign_id: str,
    query: str,
    category: str | None = None,
    top_k: int = 3,
    min_similarity: float = 0.25,
) -> list[dict[str, Any]]:
    """Query Milvus vector store filtered by campaign_id and optional category."""
    try:
        client = ensure_collection()
        query_vector = await get_embedding(query)
        filter_expr = f'campaign_id == "{campaign_id}"'
        if category:
            filter_expr += f' and category == "{category}"'

        results = client.search(
            collection_name=COLLECTION_NAME,
            data=[query_vector],
            filter=filter_expr,
            limit=top_k,
            output_fields=["campaign_id", "category", "source", "chunk_text"],
        )

        matches: list[dict[str, Any]] = []
        if results and len(results) > 0:
            for hit in results[0]:
                distance = hit.get("distance", 0.0)
                if distance >= min_similarity:
                    entity = hit.get("entity", {})
                    matches.append({
                        "source": entity.get("source", ""),
                        "category": entity.get("category", ""),
                        "chunk_text": entity.get("chunk_text", ""),
                        "score": round(float(distance), 4),
                    })
        return matches
    except Exception as e:
        logger.error(f"Milvus search error: {e}")
        return []


async def get_grounding_citations(
    campaign_id: str,
    query: str,
    top_k: int = 3,
) -> list[GroundingCitation]:
    """Retrieve top grounding citations formatted for state['analysis'].grounding_citations."""
    matches = await search_campaign_knowledge(campaign_id, query, top_k=top_k)
    return [
        GroundingCitation(
            source_id=m["source"],
            content_snippet=m["chunk_text"][:300],
            similarity_score=m["score"],
        )
        for m in matches
    ]
