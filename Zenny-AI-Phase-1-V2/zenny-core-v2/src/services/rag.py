"""
RAG / Knowledge Base Retrieval
Vector search via Supabase pgvector + optional hybrid (BM25) search.
"""

from typing import Optional

from src.services.db import get_supabase


class RAGService:
    """
    Retrieves relevant KB chunks for a user query.
    Uses pgvector cosine similarity + optional keyword fallback.
    """

    async def query(
        self,
        client_id: str,
        query_text: str,
        top_k: int = 5,
        min_freshness: float = 0.5,
    ) -> str:
        """
        Query KB and return formatted context string.

        Args:
            client_id: Tenant ID
            query_text: User message
            top_k: Number of chunks to retrieve
            min_freshness: Minimum freshness score (0-1)
        """
        # 1. Get embedding for query (using Gemini Embedding API)
        query_embedding = await self._embed_query(query_text)

        # 2. Vector search via Supabase RPC
        db = get_supabase()
        result = (
            db.rpc(
                "match_kb_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.5,
                    "match_count": top_k,
                    "p_client_id": client_id,
                }
            )
            .execute()
        )

        chunks = result.data or []

        # 3. Filter by freshness
        fresh_chunks = [c for c in chunks if c.get("freshness_score", 1.0) >= min_freshness]

        if not fresh_chunks:
            return ""

        # 4. Format context with source attribution
        formatted = "\n\n".join([
            f"[Source: {c.get('source_type', 'doc')} | Relevance: {c.get('similarity', 0):.2f}]\n{c['content']}"
            for c in fresh_chunks
        ])

        return formatted

    async def _embed_query(self, query_text: str) -> list[float]:
        """
        Generate embedding for query text.
        Uses Gemini Embedding API (models/embedding-001).
        """
        import google.generativeai as genai
        from src.config import settings

        genai.configure(api_key=settings.gemini_api_key)
        result = genai.embed_content(
            model="models/embedding-001",
            content=query_text,
            task_type="retrieval_query",
        )
        return result["embedding"]

    # ── Hybrid Search (Gap #8 — stub for future) ──

    async def query_hybrid(
        self,
        client_id: str,
        query_text: str,
        top_k: int = 5,
    ) -> str:
        """
        Hybrid search: vector similarity + BM25 keyword matching.
        TODO: Implement when Gap #8 is filled (requires tsvector column).
        For now, falls back to vector-only.
        """
        # Future implementation:
        # 1. Vector search (top_k * 2)
        # 2. BM25 search via to_tsvector (top_k * 2)
        # 3. Rerank combined results
        # 4. Return top_k
        return await self.query(client_id, query_text, top_k)


# Singleton
rag_service = RAGService()
