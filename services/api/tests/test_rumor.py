import pytest

from preza.domain.rumor import looks_like_rumor


@pytest.mark.parametrize(
    "phrase",
    [
        "reportedly",
        "according to people familiar",
        "according to persons familiar",
        "according to sources",
        "people familiar with the matter",
        "sources say",
        "sources said",
        "is said to",
        "are said to",
        "rumor",
        "rumour",
        "rumors",
        "rumours",
        "rumored",
        "rumoured",
        "unconfirmed",
        "takeover speculation",
        "in talks to",
        "in early talks to",
        "in advanced talks to",
        "exploring sale",
        "exploring a sale",
        "weighing a bid",
        "weighing offer",
        "weighing a sale",
        "domnevno",
        "neuradno",
        "po navedbah virov",
        "po neuradnih navedbah virov",
        "govorice",
        "govoricah",
        "naj bi",
    ],
)
def test_hedging(phrase: str) -> None:
    assert looks_like_rumor(f"Company {phrase} acquisition", None)
    assert looks_like_rumor(f"Company {phrase.upper()} acquisition", None)
    assert looks_like_rumor("Company update", f"Company {phrase} acquisition")


@pytest.mark.parametrize(
    "title",
    [
        "Company reports Q3 results",
        "Company reported revenue",
        "earnings report",
        "CEO talks about AI at conference",
        "Company announces acquisition",
        "",
        "unreportedly",
        "rumorous",
        "speculations",
        "naj bitje",
        "domnevnost",
    ],
)
def test_plain_reporting(title: str) -> None:
    assert not looks_like_rumor(title, None)
    assert not looks_like_rumor(title, "Published financial results")


@pytest.mark.parametrize(
    "title",
    [
        "Acme nears deal to buy Beta",
        "Acme nears a deal to buy Beta",
        "Acme in discussions to acquire Beta",
        "Acme considering takeover of Beta",
        "Acme considering a bid for Beta",
        "Acme considering acquisition of Beta",
        "Acme considering a sale of its business",
        "Acme explores sale",
        "Acme exploring options including a sale",
        "Acme explores strategic alternatives",
        "Acme approached by potential buyers",
        "Acme approached about a takeover",
        "Acme takeover advances, people with knowledge say",
        "Acme takeover advances, person familiar says",
        "Acme takeover advances, people briefed say",
        "Acme weighs bid, anonymous sources tell Reuters",
        "Acme weighing offer for Beta",
        "Acme weighs a sale of its business",
        "Acme weighing a deal with Beta",
        "Acme plans to buy Beta - sources",
        "Acme plans to buy Beta — sources",
        "Acme plans to buy Beta: sources",
        "Acme plans to buy Beta, sources",
        "Acme plans to buy Beta -source",
        "Acme rejects takeover speculation",
        "Speculation that Acme will launch a takeover grows",
        "Speculation about a merger lifts Acme shares",
        "Speculation over Acme acquisition grows",
        "Acme in exclusive talks with Beta",
        "Acme in\n  advanced\t talks  to acquire Beta",
        "Podjetje je v pogovorih za prevzem tekmeca",
        "Podjetje je v pogajanjih za nakup tekmeca",
        "Podjetje razmišlja o prevzemu tekmeca",
        "Podjetje preučuje prodajo oddelka",
        "Podjetje preučuje možnost prodaje oddelka",
        "Podjetje išče kupca po poročanju več virov",
    ],
)
def test_full_headline_rumors(title: str) -> None:
    assert looks_like_rumor(title, None)
    assert looks_like_rumor("Company update", title)


@pytest.mark.parametrize(
    "title",
    [
        "Acme reports earnings above speculation",
        "Acme presents new product in talks at developer conference",
        "Acme reports Q3 results",
        "Acme reported revenue growth",
        "Acme publishes earnings report",
        "Acme could increase production",
        "Acme plans to buy Beta",
        "Acme considering new office locations",
        "Acme weighs environmental impact",
        "Acme explores new markets",
        "Acme discusses open sources",
        "Podjetje poroča o rasti prihodkov",
        "Podjetje načrtuje nakup tekmeca",
        "Podjetje razmišlja o širitvi proizvodnje",
    ],
)
def test_full_headline_non_rumors(title: str) -> None:
    assert not looks_like_rumor(title, None)
    assert not looks_like_rumor("Company update", title)


def test_speculation_deal_context_does_not_cross_fields() -> None:
    assert not looks_like_rumor("Speculation about earnings grows", "Acme announces acquisition")
