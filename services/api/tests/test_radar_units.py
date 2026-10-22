from preza.radar.cluster import cosine, jaccard, words
from preza.radar.score import ScoreInput, opportunity_score
from preza.radar.store import canonical_url


def test_canonical_url_drops_tracking_and_fragments() -> None:
    assert (
        canonical_url("HTTPS://Example.com/a/b/?utm_source=x&id=7#top")
        == "https://example.com/a/b?id=7"
    )


def test_similarity_helpers() -> None:
    assert cosine([1, 0], [1, 0]) == 1.0 and cosine([1, 0], [0, 1]) == 0.0
    a = words("Microsoft raises full-year cloud revenue guidance")
    b = words("Microsoft raises cloud revenue guidance for the year")
    assert jaccard(a, b) > 0.5


def test_score_rewards_material_new_relevant_events_and_penalizes_rumors() -> None:
    base = ScoreInput(
        materiality=0.8, novelty=0.9, reaction_z=2.0, relevance=1.0, is_rumor=False, attention=1.0
    )
    strong = opportunity_score(base)
    assert 0.5 < strong <= 1.0
    rumor = opportunity_score(ScoreInput(**{**base.__dict__, "is_rumor": True}))
    assert rumor == round(strong * 0.6, 4)
    unknown = opportunity_score(ScoreInput(**{**base.__dict__, "relevance": 0.3}))
    assert unknown < strong
    buzz = opportunity_score(ScoreInput(**{**base.__dict__, "attention": 8.0}))
    assert buzz >= strong
