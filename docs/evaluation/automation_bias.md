# Automation and anchoring bias protocol

Hypothesis: completing an independent human first review before seeing AI findings
can reduce adoption of incorrect AI advice. This is an empirical hypothesis inspired
by [Buçinca, Malaya and Gajos (2021)](https://doi.org/10.1145/3449287), not an established
effect in ThesisHounds. Independence can also preserve an incorrect initial human
anchor; it does not remove every cognitive bias.

Randomize qualified consenting reviewers to (1) human review without AI, (2) immediate
AI assistance, or (3) independent human review followed by AI/discussion. Counterbalance
document order, avoid showing the same document twice to one reviewer and prevent
cross-condition contamination. Include expert-verified correct and incorrect advice
balanced for salience and specificity; disclose experimental procedure appropriately
and obtain ethics/privacy guidance before running a participant study.

Measure initial/final correctness per criterion, unsupported-AI adoption, appropriate
reliance, confidence, changes in rationale, time and cognitive burden. Preserve initial
reviews. Assess whether discussion improves correction or simply persuasion. Blind
adjudicators to condition. Determine sample size from an explicit power analysis;
model reviewer/document clustering and preregister exclusions and primary contrasts.

Implemented interaction controls: server embargo, no early numerical AI rating,
neutral side-by-side review, uncertainty/evidence labels, no preselected agreement,
explicit criterion decisions and final human release. No participant results,
causal benefits or bias-elimination claims exist yet.
