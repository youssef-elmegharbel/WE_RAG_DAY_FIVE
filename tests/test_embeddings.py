from rag.embeddings import get_embeddings


def test_returns_same_instance_across_calls():
    """The model is heavy; it must load once per process."""
    assert get_embeddings() is get_embeddings()


def test_embeds_a_query_to_a_fixed_length_vector():
    vector = get_embeddings().embed_query("What is a rational agent?")

    assert len(vector) == 384  # bge-small-en-v1.5 dimensionality
    assert all(isinstance(value, float) for value in vector[:5])
