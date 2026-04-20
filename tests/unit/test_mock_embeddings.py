from __future__ import annotations

from internal_assistant.llm.mock_provider import MockLLMProvider


def test_mock_embeddings_have_expected_dimension():
    provider = MockLLMProvider()
    embeddings = provider.embed_texts(["hola", "mundo"])

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 512
    assert embeddings[0] != embeddings[1]
