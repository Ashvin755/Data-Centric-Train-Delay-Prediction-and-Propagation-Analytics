# Prior Work and Comparison Notes

Supporting document for the conference paper in this directory
(`main.tex`, "Data-Centric Approach to Train Delay Prediction in Indian
Railways"). It records what each cited prior study actually reports, the
verified numbers retrieved for it, how those numbers compare with our
results, and why a direct ranking is not always meaningful.

- Prepared in response to the reviewer comment: *"Add Evaluation Tables,
  Compare results with past research."*
- All figures below were retrieved from the primary sources (arXiv HTML,
  the archived publisher PDF, Crossref/OpenAlex metadata) and are quoted as
  reported. Nothing here is estimated or extrapolated.
- The comparison subsection of the paper is `\subsection{Comparison with
  Prior Work}` in Section V (after *Time-Series Trials*, before
  *Limitations*).

---

## 1. Our results (reference point)

Target: **next-station DEPARTURE delay in minutes, per train journey**,
chronological journey-wise 80/20 split (latest 20% of journey dates held
out). Train 18238 analysis window: 1 January – 24 May 2026.

| Model | Train | MAE (min) | RMSE (min) |
|---|---|---|---|
| **TCN** | 18238 | **4.778** | **8.105** |
| LSTM | 18238 | 4.988 | 8.634 |
| XGBoost (tuned) | 18238 | 5.532 | 8.234 |
| Linear regression | 18238 | 7.160 | 10.277 |
| Ridge regression | 18238 | 7.161 | 10.275 |
| Persistence (naive) | 18238 | 8.375 | 14.190 |
| Rolling mean (3) | 18238 | 12.257 | 17.100 |
| Random forest | 11077 | 11.592 | 18.534 |
| Polynomial regression | 11077 | 12.322 | 19.082 |

Additional facts: day/night XGBoost MAE 5.485 / 6.247 min; recursive
multi-station rollout on a sample journey degrades to MAE 11.273 min; MAPE
is unusable for this target (on the order of 10^6 percent because of
near-zero denominators).

---

## 2. Prior works with verified numbers

### 2.1 Gaurav & Srivastava 2018 (zero-shot Markov model)

**Reference.** R. Gaurav and B. Srivastava, "Estimating train delays in a
large rail network using a zero shot Markov model," arXiv:1806.02825, in
*Proc. IEEE Int. Conf. Intelligent Transportation Systems (ITSC)*, 2018,
pp. 1221–1226. Bib key: `gaurav2018zeroshot`.
**Source verified:** https://arxiv.org/html/1806.02825v1 (full text).

**Task and data.**
- Predict **arrival late-minutes at in-line stations**, fed forward along
  the journey.
- 135 trains passing Mughalsarai (MGS), March 2016 – February 2018;
  819 stations (621 known); up to 334 journeys/train (average 48),
  average 30 stations per route.
- Zero-shot design: 52 *Known Trains* (CV Mar 2016 – Jun 2017, test
  Jul 2017 – Feb 2018) vs 83 *Unknown Trains*.
- Method: N-Order Markov Model with Linear/ML-based Prediction Framework
  (N-OMLMPF); per-station Random-Forest Regressor (RFR) and Ridge;
  k-NN (k=10) for unseen stations.

**Reported metrics** (4-OMLMPF RFR unless noted):

| Experiment | CI 68% | CI 95% | CI 99% |
|---|---|---|---|
| Exp 1 (known-train CV) | 34.39 | **62.53** | 71.74 |
| Exp 2 (unknown-train zero-shot) | 5.66 | **14.96** | 18.97 |
| Exp 3 | 33.67 | 61.57 | 71.49 |
| Exp 4 (known-train test) | 27.82 | **55.80** | 66.82 |

- **Mean RMSE per journey (minutes):** known trains 29.42–96.61, unknown
  trains 11.75–80.66; overall range ≈ **11.75–96.61 min**.
- Ridge is much worse than RFR (e.g. Exp 4 CI95 43.89).
- Model selection: 1st-order Markov best by AIC/BIC for 40–67% of known
  and 71–82% of unknown trains; 3rd/4th-order lowest cumulative RMSE.
- Coverage claim: their data covers 11.3% of Indian stations with 1.2% of
  trains.

**Our corresponding result:** TCN RMSE **8.105 min** (per station step,
Train 18238, held-out journeys).

---

### 2.2 Arshad & Ahmed 2019 (survey + proposed protocol, no numbers)

**Reference.** M. Arshad and M. Ahmed, "Prediction of train delay in
Indian Railways through machine learning techniques," *Int. J. Comput.
Sci. Eng. (IJCSE)*, vol. 7, no. 2, pp. 405–411, Feb. 2019,
doi: 10.26438/ijcse/v7i2.405411 (publisher ISROSET, ISSN 2347-2693).
Bib key: `arshad2019prediction`.
**Source verified:** archived publisher PDF (Wayback capture of
`ijcseonline.org/pub_paper/67-IJCSE-05874.pdf`, 7 pages, full text
extracted locally).

**Task and protocol.**
- Proposes comparing **three machine-learning methods** — multivariate
  regression, neural network, and random forest — for Indian train-delay
  prediction.
- Comparison criteria: **training time and accuracy over the test data
  set**; data split stated as 70% train / 30% test.
- The body of the paper is a literature survey (11 studies, 2010–2018)
  plus method descriptions; the conclusion is written in future tense
  ("will be able to improve accuracy").

**Reported results:** **no numeric results of its own.** The only
percentages in the paper are second-hand entries in its survey table
(e.g. Yaghini ~90% accuracy, Nilsson ~3 min average NN error,
Pongnumkul 23% error reduction).

**Our corresponding result:** TCN MAE **4.778** / RMSE **8.105 min**;
the paper gives nothing numeric to place beside them.

---

### 2.3 Chowdhury et al. 2026 — RSTGCN (station-level spatio-temporal GCN)

**Reference.** K. Chowdhury, P. Koley, A. Chakraborty, and S. Ghosh,
"RSTGCN: Railway-centric spatio-temporal graph convolutional network for
train delay prediction," *IEEE Trans. Intell. Transp. Syst.*, 2026,
doi: 10.1109/TITS.2026.3726308; arXiv:2510.01262 (v1 Sep 2025, v2 Aug
2026). Bib key: `chowdhury2025rstgcn`.
**Source verified:** https://arxiv.org/html/2510.01262v2 (full text) and
https://arxiv.org/abs/2510.01262 (author list, DOI, venue).

**Task and data.**
- Target: **hourly average arrival delay across all incoming trains at a
  station** (a spatial aggregate), horizons 1/2/3 hours; metrics in
  **hours**.
- IRN dataset: 4,735 stations, 9,336 edges, 3,892 express trains, 17
  zones; 1–30 September 2024; 1,282,326 records (source runningstatus.in).
- Split: 7 days context, then 23 days chronological 70/10/20; test from
  26 Sep 08:00. Context statistics: average arrival delay ≈ 32 min;
  25% of observations > 30 min, 13% > 1 h, 7% > 2.5 h.

**Reported results** (full-IRN averages, Table VIII):

| Model | MAE (h) | MAPE (%) | RMSE (h) |
|---|---|---|---|
| ASTGCN | 0.092 | 10.86 | 0.416 |
| TSTGCN | 0.096 | 12.20 | 0.385 |
| **RSTGCN** | **0.075** | **9.24** | **0.38** |

- Zone-averaged 1 h horizon (Table IV): RSTGCN MAE 0.074 h
  (≈ **4.44 min**), MAPE **8.53%**, RMSE 0.427 h (≈ **25.6 min**);
  best baselines STGCN/ASTGCN/TSTGCN MAE 0.090–0.098 h, MAPE 10–17%.
- Claimed improvement over best baseline: 18–21% MAE, 14–24% MAPE,
  1–8% RMSE.
- **MAPE handling:** "when the actual delay is zero, we compute the
  percentage difference directly" — an explicit zero-handling rule, which
  is the same concern that makes us report MAPE with caution.

**Our corresponding result:** TCN MAE **4.778 min** — similar magnitude
to their ≈ 4.5 min, but on a per-train departure target rather than a
station-hourly average; our RMSE **8.105 min** is far below their ≈ 22.8
min (0.38 h), reflecting the heavier tail of station-wide aggregates.

---

## 3. Prior works that could not be numerically retrieved

| Study | Bib key | Status | Why | Comparison type |
|---|---|---|---|---|
| Oneto et al. 2018, "Train delay prediction systems: a Big Data Analytics perspective," *Big Data Research* 11:54–64, doi 10.1016/j.bdr.2017.05.002 | `oneto2018train` | Closed access; no abstract indexed (OpenAlex W2618782758), no OA copy | Paywalled full text; related open book chapter (Fumeo et al., doi 10.4018/978-1-5225-3176-0.ch014) is a different paper with only qualitative claims | Qualitative: shallow/deep Extreme Learning Machines on Italian network data, "improves over current TDPSs"; weather features reported +5–10% accuracy in the survey of Arshad |
| Flier, Graffagnino & Nunkesser 2009, "Forecasting train delays using delay distributions," ATMOS 2009 | `flier2009delay` | Not findable anywhere (S2 404, search engines no result, dblp bot-walled) | Workshop paper with no accessible online copy | Qualitative: delay-distribution forecasting rather than point accuracy |
| Goverde 2010, "A delay propagation algorithm for large-scale railway traffic networks," *Transp. Res. C* 18(3):269–287, doi 10.1016/j.trc.2010.01.002 | `goverde2010railway` | Closed access; no abstract, no OA copy (OpenAlex W2079246731) | Paywalled; method paper, not an ML-accuracy paper | Qualitative: timetable-based delay propagation algorithm |

No numbers are quoted for these three anywhere in the paper, and none
should be invented for them.

---

## 4. Comparison table (as included in the paper)

| Study | Scope | Task / target | Metric | Reported result | Our result |
|---|---|---|---|---|---|
| Gaurav & Srivastava 2018 | 135 trains via Mughalsarai, 2016–2018 | Arrival late-minutes at in-line stations (feed-forward) | 95% CI coverage; per-journey RMSE (min) | Coverage 62.5% (known) / 15.0% (zero-shot); RMSE 11.8–96.6 | RMSE **8.1** (TCN) |
| Arshad & Ahmed 2019 | Indian Railways survey + proposed protocol | MR, NN, and RF compared for delay prediction | Accuracy; training time | No numeric results reported | MAE **4.8** / RMSE **8.1** |
| Chowdhury et al. (RSTGCN) 2026 | Whole IRN, 4,735 stations, Sep. 2024 | Station-hourly average arrival delay, 1 h horizon | MAE (h), MAPE (%), RMSE (h) | MAE 0.075 h (≈ 4.5 min); MAPE 9.2%; RMSE ≈ 22.8 min | MAE **4.8** min |

Oneto et al., Flier et al., and Goverde are discussed in prose only
(Section 3 above).

---

## 5. Comparability caveats

1. **Different targets.** Ours: next-station *departure* delay of a
   single train journey, in minutes. Gaurav: *arrival* late-minutes at
   in-line stations, aggregated per journey (RMSE over a whole journey's
   feed-forward predictions). RSTGCN: *average* arrival delay across all
   trains at a station per hour, in hours. Arshad: protocol without
   numbers. Oneto/Flier/Goverde: distributions and propagation, not
   point accuracy.
2. **Different scopes.** One corridor/panel (10 trains, one route each)
   vs 135 trains through one junction vs the entire 4,735-station network.
3. **Different splits.** Ours: chronological journey-wise 80/20 (latest
   20% of dates held out). Gaurav: time-block CV + zero-shot train holdout.
   RSTGCN: 7-day context + 70/10/20 chronological split.
4. **Unit conversion is necessary.** RSTGCN reports hours; converted at
   1 h = 60 min, 0.075 h ≈ 4.5 min, 0.38 h ≈ 22.8 min.
5. **MAPE is not interchangeable.** Our near-zero denominators produce
   MAPE ~10^6 %; RSTGCN avoids this with explicit zero-delay handling and
   a coarser hourly target. This is why the paper reports absolute errors
   as the meaningful indicators.

The honest framing used in the paper is therefore a **protocol-level
comparison with stated targets and a non-comparability note**, not a
ranked leaderboard.

---

## 6. Citation fixes applied with this change

In `main.tex` (hand-typed `thebibliography`):

- `arshad2019prediction`: was "M. Arshad" + ResearchGate URL → now
  **M. Arshad and M. Ahmed**, full title, *Int. J. Comput. Sci. Eng.*,
  vol. 7, no. 2, pp. 405–411, Feb. 2019, doi: 10.26438/ijcse/v7i2.405411.
- `chowdhury2025rstgcn`: was "K. Chowdhury" + arXiv only → now full
  four-author list, *IEEE Trans. Intell. Transp. Syst.*, 2026,
  doi: 10.1109/TITS.2026.3726308.

In `docs/references.bib` (used by the minor project report via BibTeX):

- Restored `gaurav2018zeroshot` (original arXiv entry), and restored
  `arshad2019prediction` / `chowdhury2025rstgcn` with the corrected
  metadata above, because the report's Chapter 2 cites all three keys.
- The two placeholder entries `india_survey_example` and
  `india_simulation_example` (marked "hypothetical reference") were left
  untouched.

---

## 7. Source / access log

| Paper | What was used | Result |
|---|---|---|
| Gaurav 2018 | arXiv HTML v1 full text | Full tables retrieved (Tables VIII–IX) |
| RSTGCN | arXiv HTML v2 + abs page | Full tables (IV, VIII) + author list + DOI |
| Arshad 2019 | Crossref metadata, Wayback landing/XML/PDF, local PDF text extraction (PyMuPDF) | Full text; confirms no original numbers |
| Oneto 2018 | OpenAlex, Crossref, related book chapter | Closed access; no numbers |
| Flier 2009 | Semantic Scholar, OpenAlex, search engines, dblp | No accessible copy exists |
| Goverde 2010 | OpenAlex, Crossref | Closed access; method paper |

Blocked/rate-limited sources encountered during retrieval: Semantic
Scholar API (429), dblp (bot wall), DuckDuckGo (CAPTCHA), Mojeek
(Altcha wall), Bing (Chrome-only), Crossref content transform (406),
Unpaywall (422), live ijcseonline.org (404), ResearchGate (403).
