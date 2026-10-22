# Prevzem iz starega projekta `PksOck/trading-list`

**Datum:** 2026-10-22 · **Seja:** S-001
**Projekt:** PHP 8.2 + MySQL na cPanelu (`view.zavadlal.com`). Watchlista, backlog, portfelj, 8 OpenAI agentov z utežno sintezo, cron za cene in opozorila po e-pošti.

> **Načelo (uporabnik, S-001):** stari projekt **ni predloga**. Preža se gradi na novo in bolje. Iz trading-list vzamemo samo **izkušnje** (kaj je delovalo, kaj ne) in **podatke** (tvoje obstoječe ideje in teze). Arhitekture, kode, UI-ja in ocenjevalne lestvice ne prenašamo.

### Kaj je bilo prej in kaj je zdaj bolje

| Področje | trading-list | Preža |
|---|---|---|
| Kdaj se analiza zgodi | ročni klik ali cron, vsaka delnica enako | dogodkovno: Radar in Vstopi sprožijo analizo samo, ko se nekaj zgodi (novica, filing, cena v coni) |
| Kdo analizira | 8 neodvisnih agentov → sinteza z utežmi | debata (bull/bear, 3 perspektive tveganja) + specializirani analitiki + deterministični izračuni |
| Številke | LLM bere in povzema številke | številke računa koda, LLM samo interpretira |
| Teza | prosto besedilo | merljive trditve, ki se tedensko samodejno preverjajo |
| Ali sistem deluje | ni merjeno | vsak signal ima izid po 1/5/20/60 dneh, kalibracija |
| Portfelj | ročni vnos pozicij | samodejno iz IBKR (Flex) |
| Novice in špekulacije | ni | Radar z lokalno triažo, govorice ločene od dejstev |
| Vstopne točke | opozorilo pod/nad ceno | cona + vzrok padca + postopni nakup + opcijska alternativa |
| Stroški | ~0,05 $ na delnico po optimizaciji | večina dela lokalno (0 $), oblak samo za eskalacije |
| Obvestila | e-pošta | Telegram z dejanji |

Spodaj je seznam izkušenj, ki jih upoštevamo. Vse je **izhodišče za izboljšavo**, ne za kopiranje.

## 1. Model watchliste → naša tabela `watchlist_item`

| Stari stolpec (`stocks`) | Pri nas | Opomba |
|---|---|---|
| `list_type` = `selected` / `backlog` | `tier` = `active` / `reserve` | dve ravni: aktivna watchlista in "zaloga" idej. Zaloga se v Radarju pokaže v pogledu *Novi predlogi* |
| `status` = `new` / `reviewed` | `reviewed_at` | značka "novo, nepregledano" |
| `source` = `ai` / `jeremy` | `source` (`manual`, `agent`, `radar`, `external:<ime>`) | od kod je ideja prišla, za merjenje uspešnosti po viru |
| `category` | `tags[]` | prosto označevanje (tema, sektor) |
| `thesis`, `main_risk` | povezava na `thesis` (trditve + "kaj bi jo ovrglo") | stara besedilna teza postane prva trditev |
| `expected_growth_5y_pct`, `target_price_5y` | `thesis.target_price`, `thesis.horizon` | dolgoročni cilj |
| `price_at_add`, `date_added`, `progress_pct` | `added_price`, `added_at`, izračunan donos od dodaje | "kako se je ideja obnesla od dodaje", hkrati vhod za Uspešnost (SCR-10) |
| `dividend_yield_pct` | iz fundamentov (ne ročno) | |
| `alert_below`, `alert_above` | `price_alert` (spodaj/zgoraj) → Telegram | ostane, poleg vstopne cone |
| `portfolio_positions` (ročni vnos) | `position` iz IBKR Flex | ročni vnos ni več potreben |

**Uvoz (neobvezno):** enkratni skript `services/api/scripts/import_trading_list.py` iz MySQL izvoza (`stocks`, `stock_analysis`) → `watchlist_item`, `thesis`, zgodovina analiz kot `agent_run` z oznako `legacy` (BL-033).

## 2. Agenti (`agents/*.md`) → dopolnitev TradingAgents

TradingAgents ima tehničnega, fundamentalnega, analitika novic in sentimenta. Stari projekt ima analitike, ki jih tam ni in so za dolgoročnega vlagatelja pomembni:

| Stari agent | Pri nas | Način |
|---|---|---|
| `04_DividendAgent` (dividende, odkupi, FCF pokritost) | `dividend_analyst` | prepis poziva, izhod po naši shemi (BL-088) |
| `06_RelativeValueAgent` (2–3 primerljiva podjetja, P/E, EV/EBITDA, PEG, 5-l. razpon) | `relative_value_analyst` | prepis poziva + deterministični izračun multiplikatorjev (BL-088) |
| `03_InsiderAgent` | del Radarja (Form 4) + kontekst | deterministično iz EDGAR, LLM samo interpretira |
| `02_MacroSectorAgent` (VIX, sektor) | kontekst za vse agente | FRED + sektorski ETF-ji |
| `08_SynthesisAgent` | ideje v `PortfolioDecision` | glej §3 |
| `01_Fundamental`, `05_Technical`, `07_Risk` | TradingAgents že pokriva | samo primerjava pozivov |

Dodatna analitika vključimo kot dodatna vozlišča pred Research managerjem (TradingAgents `graph/setup.py` ali naš ovoj, ki njune izhode doda v kontekst). Odločitev ob BL-080.

## 3. Ideje iz sinteze, ki jih dodamo v shemo odločitve

1. **Sprožilci ocene** (`rating_triggers`): pogoj za nadgradnjo in za znižanje ocene ("nadgradi na Kupi, če ..."). Postanejo **trditve teze**, ki jih thesis tracker preverja tedensko (BL-089).
2. **`delta_note`**: kaj se je spremenilo od prejšnje analize (ocena, ključni nov podatek). Prikaz na SCR-05 in SCR-06 (BL-089).
3. **Prepričanje (`conviction`) 1–10** in **velikost pozicije v razredih** (majhna < 2 %, normalna 2–4 %, povečana 4–6 %) kot vhod za predlog velikosti.
4. **Ocena "Opazuj"** (na watchlisti, čakaj na boljši vstop ali katalizator) je pri nas boljše rešena: status signala `watching` + vstopna cona v modulu Vstopi, ki pove **pri kateri ceni** in **zakaj**. Ocene ostanejo po VOICE.md §4.
5. **Utežena kompozitna ocena** (fundamenti 25 %, tehnika 15 %, relativna vrednost 15 %, tveganje 15 %, ostalo 10 %): uporabimo kot **deterministični** kontrolni izračun ob LLM oceni. Velika razlika med njima zniža zaupanje.

## 4. Izkušnje s stroški

- Prehod iz OpenAI z `web_search` (~0,67 $/delnico) na vnaprej pridobljene podatke (FMP, EDGAR, FRED) + MiniMax je znižal ceno na ~0,05 $. **Potrditev naše zasnove:** agenti dobijo podatke iz baze (`vendor_local`), ne iščejo po spletu.
- Dnevni limit 10 analiz je deloval. Pri nas: nastavljiv limit (SCR-11, privzeto 6 globokih analiz na dan).
- Fallback ponudnik (MiniMax → OpenAI) se je obnesel. Pri nas to ureja LiteLLM.

## 5. UI ideje

- Preklop kartice/seznam na watchlisti (shranjeno na pogled) → CMP-16 razširitev (BL-005).
- Hitro dodajanje simbola s kategorijo neposredno na seznamu.
- "Napredek od dodaje" kot stolpec na watchlisti.
