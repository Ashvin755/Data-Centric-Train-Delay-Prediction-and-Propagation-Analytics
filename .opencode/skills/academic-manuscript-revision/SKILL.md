---
name: Academic Manuscript Revision
description: "Audit and revise academic manuscript prose in place, in severity order, with verified citations. Load when the user asks to review, tighten, revise, rewrite, or 'fix' a paper, thesis chapter, abstract, introduction, related work, discussion, conclusion, results section, or LaTeX source; when they supply a draft and ask what is wrong with it; when they ask to de-slop or de-AI text, reduce hedging, or cut filler; or when they want references, citations, DOIs, or a .bib checked. Produces a findings list and minimal, compilable edits. OVERRIDES any default tendency toward verbose, hedged, or decorative prose."
---

# Academic Manuscript Revision

Revise existing academic prose. Produce two things: a ranked findings list, and minimal in-place edits that apply cleanly.

This skill is organized by **action**, not by rule list. Rules live inside the step that uses them, because a rule you cannot act on is noise.

---

## 1. Operating principle

**A rule firing means a claim needs adjudication. It does not mean a find-replace is due.**

The most common failure in automated revision is treating every flag as a spelling error to fix. "Replace *novel* with *proposed*" is correct 90% of the time and wrong in the case that matters most: the one place where the paper is genuinely novel. Likewise, hedging a sentence whose evidence is missing does not make the sentence supported. Hedging is calibration, not repair.

Three consequences, applied throughout:

1. **Accuracy outranks style.** Never spend an edit budget on Section 7 while an unverified citation sits in Section 6.
2. **A flag you cannot substantiate is not a finding.** Do not report "remove filler" without quoting the span.
3. **Do not edit on inference.** Read enough surrounding text to know what the author meant before changing a claim.

---

## 2. Severity ranking

Fix top-down. Stopping early is fine; reordering is not.

| Tier | Class | Examples | Action |
|---|---|---|---|
| **1** | Factual integrity | Fabricated or placeholder reference; cited source does not support the sentence; causal claim without a design permitting it; wrong or missing unit, sample size, or baseline; number contradicting another section | Fix or flag. Never silently soften into vagueness. |
| **2** | Substantive quality | Scope claim with no scope ("comprehensive", "large-scale"); verb strength exceeding the evidence; contribution claimed but never evaluated; hedged interpretation presented as mechanism | Rewrite or flag. |
| **3** | Prose mechanics | Redundancy, filler, nominalization, throat-clearing; punctuation; paragraph breaks; terminology drift; acronym discipline | Batch and sweep. Cheap, low risk. |

Tier 3 work is fast. Do not let it consume the pass. If you finish with budget left and no Tier 1 or 2 findings, say so explicitly rather than padding the report with style notes.

---

## 3. Workflow

### 3.1 Survey

Read the whole target section before touching any sentence. Revision without context produces locally correct, globally incoherent text.

Establish, and state back to the user:

- The document class and what it implies (venue, length limits, two-column vs single, thesis vs conference).
- The section's job in the argument. A related-work paragraph and a results paragraph have different correct shapes.
- Which claims are load-bearing (the contribution list, the headline result, the abstract's numbers). These get Tier 1 attention first.
- Where numbers come from. If the manuscript has tables, know which table backs which sentence before you touch either.

### 3.2 Triage and confirm scope

Produce the findings list **before** editing. Then confirm scope with the user unless they already asked for a full pass. Offer the tiers explicitly, because a user who wants only Tier 3 should not get a rewrite of their argument.

Findings list format is in Section 10.

### 3.3 Verify

Run Section 5 (claims) and Section 6 (references, including online resolution) before editing. Findings from verification feed the findings list; they do not trigger edits on their own without triage.

### 3.4 Edit

Follow Section 4 without exception. It is short because it is the part that breaks documents.

### 3.5 Self-check

After editing:

- **Brace and environment balance.** Count `\{` and `\}`; confirm every `\begin{env}` has a matching `\end{env}`. Do this per edit, not once at the end.
- **LaTeX compiles.** If a toolchain is available, build the document. If not, say so; do not imply it was verified.
- **Numbers still match.** Confirm no figure, percentage, sample size, or citation key was altered by an edit.
- **Read the edited passages aloud.** If you run out of breath, split the sentence.
- **Re-check internal consistency.** An edit in one section frequently invalidates a parallel sentence in another. Search for it.

### 3.6 Report

Section 10. Report what was changed, what was flagged but not changed, and what remains unverifiable.

---

## 4. Edit protocol

### 4.1 Minimal diff

- Change only what a finding requires. Do not improve adjacent sentences you were not asked about.
- Preserve the author's line wrapping. Re-wrap only the lines you actually changed, and match the surrounding wrap column. A reflowed paragraph makes the diff unreadable and hides the real edit.
- Prefer rewriting a sentence over restructuring a paragraph. Prefer a clause over a new paragraph.
- Do not reformat tables, reorder equations, renumber sections, or touch citations unless that is the finding.

### 4.2 LaTeX safety

Never edit inside any of these without explicit instruction:

- Math mode: `$...$`, `$$...$$`, `\[...\]`, `\(...\)`
- Command arguments that carry structure: `\cite{}`, `\citep{}`, `\ref{}`, `\eqref{}`, `\label{}`, `\footnote{}`, `\includegraphics{}`, `\bibitem{}`
- Environment bodies: `\begin{itemize}`, `\begin{table}`, `\begin{figure}`, `\begin{verbatim}`, `\begin{lstlisting}`, custom macros
- Escaped characters: `\%`, `\&`, `\_`, `\$`, `\#`

Inside prose you may edit freely, with care:

- **Brace balance.** An unbalanced brace from a deleted `}` produces a LaTeX error that does not point at your edit.
- **Quotes.** Replacing a quoted phrase can unbalance a pair of `` ` `` and `''`. Recount them.
- **Cross-references.** If the edit changes a referenced label, table number, or figure number, every `\ref` to it must be checked.
- **Hyperref and labels.** Never delete a `\label{}`; a deleted label turns `\ref` into `??` silently.

If the only way to fix a sentence is to edit inside a protected construct, stop and report the finding instead of forcing it.

### 4.3 When minimal diff is impossible

Some findings cannot be expressed as a local edit: a paragraph that contradicts another, a claim that needs a number that does not exist anywhere in the manuscript, an argument whose order is wrong.

In those cases: do not improvise. Report the structural finding with a concrete proposed restructuring, and let the author decide. Inventing a number, a reference, or a mechanism to make an edit possible is the one unrecoverable error this skill exists to prevent.

---

## 5. Claim integrity

Tier 1 and Tier 2 findings. Tier 1 rules apply to every sentence in the manuscript.

### 5.1 The three-part claim test

Every load-bearing sentence should be decomposable into:

1. **Subject** — the specific system, method, dataset, or population. Not "the model" when there are four.
2. **Predicate** — the claim, at a strength matched to evidence.
3. **Basis** — the citation, table, figure, or measurement that supports it.

A sentence missing part 3 is not automatically wrong, but it must be *simple* enough that the reader's own knowledge supplies it. A sentence claiming a performance result, a causal relationship, or a scope is not recoverable without part 3.

### 5.2 Evidence-matched verbs

Match the verb to the design. This is the single highest-yield Tier 2 fix.

| Verb | Requires | Typical setting |
|---|---|---|
| prove | Formal proof or theorem | Almost never in empirical work |
| demonstrate | Design excludes the plausible alternatives | Controlled experiment, ablation, benchmark with a strong baseline |
| show | Results consistent with the claim, alternatives unlikely given the design | Standard well-controlled experiment |
| indicate | Confounders present or unmeasured | Observational, semi-controlled |
| suggest | Evidence incomplete or preliminary | Exploratory, small n, single dataset |
| imply | Follows from other results but not directly tested | Inference from a result already established |

"Prove" and "demonstrate" in an empirical results section are almost always overclaims.

### 5.3 Hedging that names the uncertainty

Two kinds:

- **Calibrated.** Names the specific source of uncertainty. "This estimate may be biased by the absence of dry-season measurements." "The 95% CI includes zero, so the effect is not distinguishable from no effect at this sample size."
- **Vague.** Names nothing. "More research is needed to fully understand this complex and dynamic issue." "Future work may explore this further."

Test: can the reader name the gap, question, or design requirement that would close it? If not, the hedge is filler. Delete it or replace it with a specific one.

**Hedge stacking.** One hedge is calibration; three is mush. "may possibly suggest that it could potentially" becomes "may suggest".

**Softening the wrong direction.** Do not hedge a mechanism you have evidence for, and do not assert one you do not. The hedge table below is a *default against overclaiming*, not a blanket weakening. When the author hedges in the *under*-claiming direction and the evidence is direct, restore the strength.

| Avoid | Prefer | Note |
|---|---|---|
| ensure, guarantee | encourage, promote | Unless formally proven |
| demonstrates that X is | shows that X | Per 5.2 |
| the most prominent | a prominent | |
| too large to deploy | difficult to deploy | |
| demand | require, benefit from | |
| optimal | effective, favourable | Unless searched |
| novel | new, proposed | **Keep if novelty is real and scoped.** See 5.6. |
| state-of-the-art | competitive, strong | Keep if verified against a current leaderboard |
| significantly (as "important") | substantially, markedly | See Section 7.6 |

### 5.4 Causal language

Do not use causal language for correlational or observational data. "X was associated with Y" is not "X caused Y". AI-generated prose slips into causal framing without a design that permits causal inference; this is one of the most reliable tells in review.

When interpreting an observed effect, state the observation first, then frame the explanation as a hypothesis:

```
Adding more data did not consistently improve performance. This may be because
models trained on larger data are pushed further apart in the weight space,
degrading interpolation.
```

Observation first, hedged cause second, explicitly numbered when there are several. This is distinct from 5.3: 5.3 governs claims about your own method, this governs interpretation of why a pattern occurred.

### 5.5 Numbers

Any quantitative claim carries these where applicable. Missing pieces are Tier 1 findings.

- Magnitude, with units, in the right unit (accuracy points vs. percent relative).
- The baseline or comparator.
- Sample size.
- The population, dataset, corpus, benchmark, or operating condition.
- Uncertainty: variance, CI, or repeated-run spread. A single point estimate presents false precision.
- Test statistic and exact p-value where a significance claim is made. `p < 0.05` alone is insufficient when the exact value is obtainable.

**Do not interpret a non-significant result as evidence of no effect.** Report the interval or the achieved power and state what it does and does not exclude.

**Do not drop a measured value to make a sentence shorter.** If a sentence is too long because it carries six numbers, split the sentence, do not delete a number.

If the manuscript claims a number it does not contain, flag it. Do not estimate, interpolate, or carry it over from a similar setup.

### 5.6 Scope and novelty

- **Scope claims need scope.** "A comprehensive analysis" is empty without how many sites, what range, what period, what methods.
- **Vague quantifiers are findings.** "Many studies have found", "several authors have argued", "numerous" → cite the specific studies or give a count.
- **Novelty claims are falsifiable.** "This is the first study to..." becomes wrong the moment one appears. Use "To our knowledge, the first in [specific domain/region/population] to..." and only after searching. Blanket bans on the word *novel* are wrong; unverifiable blanket novelty claims are the actual defect.
- **Absolutist quantifiers** ("every", "always", "never", "all") doing vague universal work are usually overstatement and are also future-falsification traps. Qualify with the scope actually studied.

### 5.7 Attribution boundaries

Three conflations to catch:

- **Producer vs consumer.** An encoder produces representations; a classifier consumes them. "BERT achieves strong ASR performance" is wrong. "BERT features improve downstream ASR word error rate" is right.
- **Artifact vs generator.** Do not write "we fine-tune the representation" when you mean the model that produces it.
- **Domain vs category.** Name tasks individually ("ASR, intent classification, emotion recognition"), not aggregated ("five speech tasks"), when the count is doing argumentative work.

---

## 6. Reference integrity

The highest-severity finding class, and the one most often missed. Fabricated references survive every style pass.

### 6.1 Inventory

Build the full set before checking anything:

- Every `\cite{}` key used in the source.
- Every entry key in the `.bib`.
- **Cited but missing** (compile error, or the author forgot).
- **Present but uncited** (harmless in BibTeX, but usually a sign the text was cut and the bib was not).
- **Duplicate keys** across files, or duplicated fields within an entry.

### 6.2 Structural checks

Run these offline; they are fast and deterministic.

- Brace and quote balance in each entry.
- Entries missing `author`, `title`, or `year` where the entry type requires them.
- `@article` entries with no `journal`; `@inproceedings` with no `booktitle`; arXiv `eprint` fields with no `archivePrefix`.
- Multiple entries sharing a suspiciously similar title or author list (a sign of one paper split into two).
- Unused fields such as `note = {TODO}`, `abstract = {...}` left in place.

### 6.3 Placeholder scan

Scan for markers of unverified or invented entries. This catches the common case before any network call.

| Pattern | Example |
|---|---|
| Literal placeholder words in metadata | `journal = {Journal of X (hypothetical reference)}`, `title = {... example}`, `placeholder`, `dummy`, `fake`, `sample reference` |
| Key names that are descriptive rather than bibliographic | `india_survey_example`, `some_paper`, `ref1`, `citation_needed` |
| Suspiciously round page ranges | `pages = {1--10}`, `pages = {45--58}` on a broad survey |
| Author names that read as constructed | `Smith, J.` / `Doe, A.` / `Author, A.` |
| Absent identifiers on a specific claim | a result, dataset, or standard attributed with no `doi`, no `eprint`, no `url` |
| Unusual year | year in the future relative to submission, or wildly older than the body of work |
| TODO markers near citations | `% TODO: add citation`, `needs a reference` |

Any hit is a **Tier 1 finding**. Do not delete the entry silently; the in-text sentence may still need it, and the author needs to choose a real replacement.

### 6.4 Online resolution

Resolve each reference against the live source. Order by stakes, not by file position: references backing the abstract, the contributions, and the headline result first.

| Entry type | Resolve via |
|---|---|
| `doi` | Fetch `https://doi.org/<doi>`; confirm it lands on a real record |
| `eprint` / arXiv | Fetch `https://arxiv.org/abs/<id>`; confirm title and authors match |
| `url` (data portal, standard, dashboard) | Fetch; confirm it resolves and is what the citation claims |
| No identifier | Search by exact title; a title that returns nothing is a fabrication candidate |

Record a verdict per reference:

- **RESOLVED** — identifier resolves and the metadata matches the record.
- **MISMATCH** — resolves, but authors, year, venue, or title differ from the `.bib` entry.
- **UNRESOLVED** — identifier does not resolve, or no record matches. Treat as fabricated until proven otherwise.
- **UNVERIFIABLE** — no identifier and no searchable record (common for internal reports, unpublished data, personal communication). Not automatically wrong; must be labeled as such in the text.

### 6.5 Claim-source match

Resolution is not endorsement. A real DOI can be attached to a sentence it does not support.

For every Tier 1 claim:

1. Read the cited source's abstract.
2. Locate the specific finding the sentence relies on.
3. Confirm the source actually makes that claim, with that scope.

Additional checks from experience:

- **Cite the describing paper, not the using paper.** If Smith (2020) applied van Genuchten (1980), cite van Genuchten (1980) for the method.
- **Do not cite a review for a claim that originates in a primary study.** Trace it down.
- **Stacked citations** (five papers for a basic fact) suggest none were read. Two well-chosen primary sources beat five.
- **"The literature suggests" with no citation** is not acceptable. Name the study or delete the sentence.
- **Label preprints** as such, and note that peer review has not occurred.
- **Date negative scope claims.** "No study has examined..." becomes wrong immediately. Use "As of [year], no published study has examined..., within [search scope]".

### 6.6 When a reference fails

Do not substitute a similar-looking real paper. That converts an obvious error into a subtle one, which is strictly worse.

Instead: delete or mark the in-text citation, and report the claim as **unsupported pending a real source**, with a concrete description of what kind of source is needed. `\textcolor{red}{needs citation}` or an equivalent author-facing marker is appropriate when the document has a convention for it.

---

## 7. Prose defects

Tier 3. Batch these, sweep them in one pass, and do not let them drive the report.

### 7.1 Structural

- **One idea, one sentence.** If a sentence carries more than two commas and two distinct claims, split it.
- **No redundant restatement.** Never restate an idea across consecutive sentences or sections. A forward reference suffices. The clearest signal: a Section 2.2 that re-argues what Section 2.1 established.
- **No duplicate lists.** If the tasks are enumerated once, do not enumerate them again later. The full enumeration belongs in one place.
- **One unifying idea, one statement.** State it once; do not re-explain it in every chapter's introduction.
- **Every acronym expanded on first use**, including common ones.
- **Complete sentences.** Subject and verb. No fragments, no telegraphic phrasing.
- **No ambiguous pronouns.** "This", "they", "it" must have an unambiguous antecedent; otherwise name the noun.

### 7.2 Filler and throat-clearing

| Remove | Do instead |
|---|---|
| "It is important to note that..." | State the point. |
| "It is worth mentioning/stressing that..." | State it or delete it. |
| "It should be noted that..." | State the content. |
| "Interestingly / Notably / Remarkably / Crucially / Importantly" | State the finding; let the reader judge interest. |
| "In today's world / In the current landscape / In recent years" | State the actual condition with a date or source. |
| "It turns out that..." / "The real reason is..." | State the finding; the framing adds nothing. |
| "Furthermore / Moreover / Additionally / Besides / In addition" | Delete unless the sentence genuinely adds a new dimension needing signposting. |
| "In order to" | "To" |
| "Due to the fact that" | "Because" |
| "In the context of" | "In", "For", or delete |
| "It can be seen that" / "We can observe that" | State the observation directly. |
| "With regard to / In terms of" | "For", "About", or delete |
| "A number of" | "Several", "many", or the actual count |
| "The majority of" | "Most" |
| "At this point in time" | "Now", "Currently" |
| "In close proximity to" | "Near" |
| "A total of 47 samples" | "47 samples" |

**Emphasis connectives exception.** "Notably", "Crucially", "Hence", "Thus" are acceptable when they mark a genuine logical turn or a non-obvious implication. At most once per subsection, and only where the sentence would lose emphasis without it.

**Binary contrast, the "not X, it's Y" cadence.** A strong tell when used for rhetorical effect: "This is not just a correlation, it's a causal mechanism." State Y directly. Two related variants collapse: "not just X but also Y" usually becomes "both X and Y", and negative listing ("Not an A effect. Not a B effect. A C effect.") is a runway the reader does not need.

The legitimate exception is a genuine contrastive finding: "The effect was driven by temperature, not by water stress." That is normal scientific content. The defect is the empty rhetorical version, not the substantive one.

**Meta-commentary.** Performative asides ("Plot twist", "As we'll see", "Let me walk you through") are filler. Functional signposting in a thesis or long report ("Section 3 describes the model; Section 4 reports the calibration results") is standard and expected. Keep the structural, cut the performative.

**Grant-proposal jargon.** "The research landscape", "navigate the challenges", "deep dive", "game-changer", "leverage", "utilize", "showcase", "delve into" → plain equivalents.

**Vague declaratives.** "The reasons are structural." "The implications are significant." Name the specific reason or implication, or cut the sentence.

### 7.3 Wordiness

**Cut dead words, never cut content.** Removing a word that carries no information is always safe, anywhere in the sentence. Removing a number, unit, parameter, procedural step, or citation is never acceptable, even if the sentence becomes dense. A dense correct sentence beats a clean incomplete one.

**Nominalizations.** Recover the verb when the noun form adds words without adding precision.

| Wordy | Concise |
|---|---|
| "performed a measurement of" | "measured" |
| "conducted an analysis of" | "analyzed" |
| "carried out an investigation of" | "investigated" |
| "made a comparison between" | "compared" |
| "gave a description of" | "described" |
| "showed a reduction in" | "reduced" |
| "is in agreement with" | "agrees with" |

Exception: some nominalizations are the correct technical term ("the calibration was poor", "soil respiration"). Recover the verb only when nothing is lost.

**Pleonasm.** "end result", "absolutely essential", "completely eliminated", "past history", "red in color", "large in size", "basic fundamentals".

**Expletives.** "There is/are X that..." and "It is X that..." bury the subject. "There are three factors that affect yield" → "Three factors affect yield." Leave "It was found that..." alone; that is conventional passive, not padding.

### 7.4 Punctuation

- **No em dashes or en dashes as parenthetical punctuation.** Restructure, or use a comma, a colon, or parentheses. "The model -- which was calibrated on 30 years of data -- performed well" → "The model, calibrated on 30 years of data, performed well."
- **No clause-introducing colons.** Colons before lists and before formal definitions are fine. A colon that introduces an explanation where a full stop would do is a defect. "We observed opposing sensitivities: configuration A improves one and degrades the other" → two sentences.
- **Minimal parentheses.** Acronym definitions, citations, and short factual asides only. If an explanation needs parentheses, it needs its own sentence.
- **Hyphens** for compound adjectives only ("field-measured data", "long-term experiment"). En dashes for numeric ranges and multi-word compound modifiers. Not sentence punctuation.
- **Capitalisation.** Do not capitalise common nouns or compound terms unless they are proper nouns or established names. "audio large language models", not "Audio Large Language Models". Benchmark and dataset names are the exception.

### 7.5 Voice and tense

**Passive voice is not a defect.** "Samples were collected to 1 m" and "the model was calibrated against field data" are standard and correct. Converting every passive to active is a well-known over-correction; leave procedural passive alone.

The one voice pattern worth flagging is an **interpretive claim that hides its agent**. A sentence arguing a conclusion is stronger when it names who is arguing: "We interpret the yield decline as water stress" over "The yield decline may be interpreted as water stress." Offer this as a suggestion, not an automatic rewrite, since some venues require the impersonal form.

**Tense is judged per sentence, by what the sentence does.** Actions performed take past tense ("we measured", "samples were collected"). Established facts and figure or table descriptions take present tense ("clay content increases water retention", "Figure 2 shows"). Objectives may take future tense, sparingly. Flag internal inconsistency and function mismatch only, never a section label.

### 7.6 Paragraph cohesion

Two rules pull in opposite directions. Both are real; resolve them by paragraph role.

- **Every paragraph needs at least two sentences.** A single-sentence paragraph either expands or merges.
- **Do not over-fragment.** One logical movement must not be split across consecutive paragraphs. The signal: two consecutive paragraphs with the same grammatical subject (or referring to it by pronoun), the second opening contrastively with "Despite", "However", "Although", or "Nonetheless" against the first. Merge them.

The counter-rule: when the second paragraph introduces a new subject, a new claim, or a list that justifies its own paragraph for visual scanning, keep the break. Merging is the default only when the logical movement is continuous.

### 7.7 Term choice

**Technical versus rhetorical use.** Many flagged words are legitimate technical vocabulary. The test is whether the word does technical work or rhetorical work.

| Term | Technical | Rhetorical |
|---|---|---|
| robust | "a robust estimator resists outlier influence" | "our approach is robust and effective" |
| optimize | "we optimized soil water parameters using PEST-HP" | "we optimized our approach for best results" |
| facilitate | "mycorrhizae facilitate P uptake by extending the root absorption zone" | "this framework facilitates knowledge transfer" |
| enhance | "biochar increased water retention by 18% (p < 0.01)" | "this study enhances our collective understanding" |
| comprehensive | "47 soil series across Peninsular Malaysia, 2018-2024" | "a comprehensive review of the literature" |
| significant | "significantly higher bulk density (p < 0.001, F = 18.4, n = 45)" | "a significant finding for the discipline" |

**Terms almost never technical in this register:** "delve", "underscore" (verb), "pivotal", "crucial", "transformative", "groundbreaking", "seamless", "holistic", "actionable", "cutting-edge". Replace with a specific, data-supported claim.

**"Significant" versus "substantial."** "Significant" means statistically significant: a formal test rejected the null at a stated alpha. It does not mean important. Use "substantial", "marked", or report the effect size directly. Never write "highly significant" without the exact p-value.

**Adverbs.** Remove adverbs doing rhetorical work (clearly, notably, interestingly, remarkably, importantly, crucially, fundamentally, inherently, inevitably, undoubtedly). Keep adverbs doing technical work (statistically, approximately, respectively, significantly in the formal sense, spatially, temporally).

### 7.8 Two things this skill will not do

- **Detect authorship.** Vocabulary clustering is not proof that a text was machine-generated. Human heuristics for this are demonstrably unreliable. Use this skill to improve writing, never to adjudicate who wrote something or to accuse a colleague.
- **Judge research design.** This skill covers prose, not whether the experimental design is valid, whether the statistics are the right choice for the design, or whether the causal story holds. Design validity is a separate review.

---

## 8. Rule conflicts

When two rules in this skill disagree, resolve as follows.

| Conflict | Resolution |
|---|---|
| Hedge table says soften vs. the evidence is strong | Match to evidence, not to the table. Hedge is a default against overclaiming, not a mandate to under-claim. |
| "novel" is on the avoid list vs. the work is genuinely novel | Keep it, but scope it (5.6). The ban targets unverifiable novelty claims, not the word. |
| Prefer active vs. leave passive alone | Leave procedural passive (7.5). Only rewrite when an agent is being hidden in an interpretive claim. |
| Cut filler vs. preserve content | Never resolves in favor of cutting. Cut dead words only (7.3). |
| Paragraphs need ≥2 sentences vs. do not over-fragment | Resolve by paragraph role (7.6). Single logical movement stays one paragraph. |
| Concise vs. complete | Split the sentence instead of dropping the content. |
| American vs. British spelling | Follow the target venue's author guidelines. Be consistent within the manuscript. Do not mix. Note: this skill does not mandate either. |

When a conflict is not covered here, prefer the reading that preserves the author's factual claims and the document's compilability over the reading that is stylistically tighter.

---

## 9. Spacing, notation, and formatting

Applies when the manuscript is LaTeX and the venue has conventions.

- **Notation consistency.** Scalars italic and non-bold. Vectors bold lowercase. Matrices bold uppercase. Functions plain italic. Sets and spaces calligraphic. Check that every symbol is defined on or near first use.
- **Every equation needs a preceding complete sentence** saying what it computes. The reader must never meet an equation without knowing its purpose.
- **Figure and table captions** should be readable without the body text. State what is shown and the units, not what the section is about.
- **Line-break hygiene in the source.** Keep prose wrapped consistently. Do not leave a paragraph as one 400-character line because an edit reflowed it.

---

## 10. Report format

End every pass with this, in this order. Keep it short enough to be read.

```
## Findings

### Tier 1 - factual integrity
1. [section/line] <one-line statement of the defect>
   Quote: "<the offending span>"
   Fix: <concrete proposed change, or why it cannot be fixed>
   (repeat)

### Tier 2 - substantive quality
...

### Tier 3 - prose mechanics
... (grouped by type, not one line each)

## Reference verification
| Key | Verdict | Note |
|---|---|---|
| oneto2018train | RESOLVED | |
| india_survey_example | UNRESOLVED | No record found for this title. In-text claim at Intro now unsourced. |

## Changes applied
- <file>:<line> - <what changed and why>

## Not changed / needs author input
- <finding> - <what is needed: a real citation, the measured number, a decision about scope>

## Verification status
LaTeX build: <passed / not run - no toolchain available>
Internal consistency: <what was re-checked>
```

Rules for the report:

- Every finding quotes the span it is about. No quote, no finding.
- Group Tier 3. Twenty separate "remove filler" lines is a report nobody reads.
- State what was not verified, as explicitly as what was. A clean report that skipped the build is worse than a dirty one that admits it.
- Never report a fix you did not make, and never silently drop a finding you could not fix.