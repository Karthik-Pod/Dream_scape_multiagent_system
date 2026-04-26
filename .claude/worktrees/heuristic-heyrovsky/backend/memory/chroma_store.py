"""
memory/chroma_store.py
───────────────────────
ChromaDB vector memory — the thesis-specified memory architecture.

Two collections:
  1. story_segments  — searchable story history
  2. character_facts — character trait/event embeddings

Agents use semantic search to retrieve relevant context
rather than blindly injecting the entire story history.
This solves the context window limitation discussed in the thesis.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import chromadb
from chromadb.config import Settings
from loguru import logger
from config import get_settings


class ChromaStore:
    """
    Vector memory store using ChromaDB.
    Provides semantic search over story segments and character facts.
    """

    def __init__(self):
        settings = get_settings()

        # Persistent client — data survives restarts
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        # Two collections per thesis architecture
        self.story_collection = self._client.get_or_create_collection(
            name="story_segments",
            metadata={"description": "Story segments with embeddings for semantic retrieval"},
        )
        self.character_collection = self._client.get_or_create_collection(
            name="character_facts",
            metadata={"description": "Character facts, traits, and events"},
        )

        logger.info(f"ChromaDB initialized at: {settings.chroma_persist_dir}")

    # ── Story Segment Operations ──────────────────────────────────

    def add_segment(self, segment_id: str, text: str, metadata: dict) -> None:
        """
        Store a story segment with metadata for filtering.
        metadata: {round, agent, arc_stage, emotional_tone}
        """
        self.story_collection.upsert(
            ids=[segment_id],
            documents=[text],
            metadatas=[metadata],
        )
        logger.debug(f"Segment stored in ChromaDB: {segment_id}")

    def search_segments(self, query: str, n_results: int = 3, filter_meta: dict = None) -> list[dict]:
        """
        Semantic search over story history.
        Use this when agents need to recall relevant past events.
        """
        kwargs = {"query_texts": [query], "n_results": n_results}
        if filter_meta:
            kwargs["where"] = filter_meta

        results = self.story_collection.query(**kwargs)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        return [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(docs, metas)
        ]

    # ── Character Fact Operations ─────────────────────────────────

    def add_character_fact(self, fact_id: str, text: str, character: str) -> None:
        """Store a character fact or event."""
        self.character_collection.upsert(
            ids=[fact_id],
            documents=[text],
            metadatas=[{"character": character}],
        )

    def search_character_facts(self, query: str, character: str = None, n_results: int = 3) -> list[dict]:
        """Retrieve relevant character history."""
        kwargs = {"query_texts": [query], "n_results": n_results}
        if character:
            kwargs["where"] = {"character": character}

        results = self.character_collection.query(**kwargs)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        return [{"text": doc, "metadata": meta} for doc, meta in zip(docs, metas)]

    def get_collection_stats(self) -> dict:
        return {
            "story_segments": self.story_collection.count(),
            "character_facts": self.character_collection.count(),
        }
