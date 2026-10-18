from __future__ import annotations

from functools import lru_cache

from app.services.text_preprocessor import keyword_score, keywords


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _lexical_similarity(left: str, right: str) -> float:
    left_words, right_words = keywords(left), keywords(right)
    if not left_words or not right_words:
        return 0.0
    # Dice similarity is deliberately named as lexical fallback, never semantic AI.
    return 2 * len(left_words & right_words) / (len(left_words) + len(right_words))


def compare(change: str, requirements: list[str], model_name: str) -> tuple[list[float], str]:
    try:
        model = _load_model(model_name)
        vectors = model.encode([change, *requirements], normalize_embeddings=True)
        similarities = [max(0.0, min(1.0, float(vectors[0] @ vector))) for vector in vectors[1:]]
        return similarities, f"Sentence Transformers ({model_name})"
    except Exception:
        return [_lexical_similarity(change, requirement) for requirement in requirements], "Lexical fallback (Sentence Transformers unavailable)"


def fallback_notice(mode: str) -> str | None:
    if mode.startswith("Lexical"):
        return "Semantic model unavailable; scores use lexical overlap and explicit dependency rules. Install sentence-transformers and download the configured model for semantic comparisons."
    return None
