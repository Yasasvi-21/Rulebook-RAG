# Rulebook RAG


A retrieval-augmented QA system over board and card game rulebooks.

The rulebooks are not included in this repo (copyright belongs to the publishers).
Download them from the links below into `data/raw/` using the file names shown.

| Game | File | Source | Type | Accessed |
|---|---|---|---|---|
| CATAN | `catan.pdf` | [CATAN – The Game Rulebook (PDF)](https://www.catan.com/sites/default/files/2025-03/CN3081%20CATAN–The%20Game%20Rulebook%20secure%20%281%29.pdf), linked from [catan.com game rules](https://www.catan.com/understand-catan/game-rules) | Official PDF (6th ed., v6.250401) | 2026-10-13 |
| Monopoly | `monopoly.pdf` | [Hasbro C1009 instructions (PDF)](https://instructions.hasbro.com/api/download/C1009_en-us_monopoly-board-game-for-ages-8-for-2-6-players-includes-8-tokens-tokens-may-vary.pdf), from [Hasbro instructions page](https://instructions.hasbro.com/en-us/instruction/monopoly-board-game-for-ages-8-for-2-6-players-includes-8-tokens-tokens-may-vary) | Official PDF, **UK edition** board and wording | 2026-10-13 |
| Blackjack | `blackjack.pdf` | [Bicycle Cards: Blackjack](https://bicyclecards.com/how-to-play/blackjack) | Web page saved as PDF | 2026-10-13 |
| Poker | `poker.pdf` | [Bicycle Cards: Basics of Poker](https://bicyclecards.com/how-to-play/basics-of-poker) | Web page saved as PDF | 2026-10-13 |
| Texas Hold'em | `texas_holdem.pdf` | [Bicycle Cards: Texas Hold'em](https://bicyclecards.com/how-to-play/texas-holdem-poker) | Web page saved as PDF | 2026-10-13 |
| Rummy | `rummy.pdf` | [Rummy Basics](https://www.rummyrulebook.com/pages/rummy-basics/) + [Standard Rummy](https://www.rummyrulebook.com/pages/standard-rummy/) | Manual copy of both pages into Google Docs, exported as PDF | 2026-10-13 |

Web pages can change. The eval set in `eval/questions.csv` was written against the versions accessed on the dates above.


## Design decisions
No game named → answer per game, labeled; retrieve per game and include only games with evidence.

## Results

| Version | Change | Recall@5 | Notes |
|---|---|---|---|
| v1 | Dense baseline (all-MiniLM-L6-v2, 800-char chunks) | 0.89 (31/35) | All 4 misses ranked 6–10 |
| v1 | Dense baseline | 0.89 (31/35) | Recall@10 = 1.00; all misses ranked 6–10 |
| v2 | + Cross-encoder reranker (ms-marco-MiniLM-L-6-v2) on top 10 | 1.00 (35/35) | Fixed all 4 v1 misses, no regressions |

| Version | Change | R@1 | R@3 | R@5 | Notes |
|---|---|---|---|---|---|
| v1 | Dense baseline (MiniLM, 800-char chunks) | 0.66 | 0.89 | 0.89 | all misses ranked 6–10 |
| v2 | + cross-encoder reranker on top 10 | 0.74 | 0.97 | 1.00 | +X ms/query |