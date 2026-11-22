# CHANGES v1h: citations for the dengue burden sentence and the Taiwan sentence

Two sentences changed; nothing else in the text files. Three bib entries added to `refs_v1.bib` (keys checked unique; 74 entries). The old entries `gbd2023diseases` and `ihme2023gbdresults` stay in the .bib file but are no longer cited in the main text. All sources were read on 2026-11-21. PubMed and the Nature page were not reachable (reCAPTCHA / login redirect), so the Bhatt abstract and the Shang full text were read on Europe PMC, which carries the same record.

## 1. Introduction (`01_introduction.md`, paragraph 1)

Old:
> The Global Burden of Disease study estimated [to be completed] dengue cases and [to be completed] deaths worldwide in [to be completed] [@gbd2023diseases; @ihme2023gbdresults]. `<!-- AUTHORS: GBD numbers ... -->`

New:
> An estimated 390 million dengue infections occur each year, and 96 million of them cause symptoms [@bhatt2013global]. Cases reported to the World Health Organization reached a record of more than 14.6 million in 2024, with more than 12,000 deaths [@who2025dengue].

(Each sentence is followed by a `<!-- src: -->` comment.)

Sources:
- `bhatt2013global`: Bhatt S, et al. The global distribution and burden of dengue. Nature 2013;496(7446):504–507. doi:10.1038/nature12060, PMID 23563266.
  - Quote 1 (abstract): "390 million (95% credible interval 284-528) dengue infections per year"
  - Quote 2 (abstract): "of which 96 million (67-136) manifest apparently"
  - URLs: https://doi.org/10.1038/nature12060 ; read at https://europepmc.org/article/MED/23563266
- `who2025dengue`: World Health Organization. Dengue and severe dengue. Fact sheet, 21 August 2025.
  - Quote (Global burden section, on 2024): "historic high of over 14.6 million cases and more than 12 000 dengue-related deaths"
  - The record wording is also supported by "more cases of dengue were recorded than ever before"; "reported to WHO" by "the number of cases reported to WHO increasing".
  - URL: https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue

Numbers: 390 million, 96 million, 14.6 million, 2024 and 12,000 each match the source text exactly. Only the thousands separator changed ("12 000" to "12,000").

## 2. Discussion (`05_discussion.md`, section 4.2, last sentences of the Taiwan paragraph)

Old:
> Dengue is also not endemic in Taiwan. Local transmission follows imported cases and is concentrated in a few southern cities, so environmental similarity to endemic districts says little about local risk.

New:
> Dengue is also not endemic in Taiwan, where imported cases can start local epidemics and local cases are concentrated in Tainan, Kaohsiung and Pingtung in the south [@shang2010imported]. Environmental similarity to endemic districts therefore says little about local risk.

Rewording: the source says imported cases "are able to" start local epidemics (when weather is favourable), so "follows" became "can start". The source names three southern areas (Tainan, Kaohsiung and Pingtung; Pingtung is a county, not a city), so "a few southern cities" became the three names. The final clause is our own inference and carries no citation.

Source:
- `shang2010imported`: Shang C-S, Fang C-T, Liu C-M, Wen T-H, Tsai K-H, King C-C. The role of imported cases and favorable meteorological conditions in the onset of dengue epidemics. PLOS Negl Trop Dis 2010;4(8):e775. doi:10.1371/journal.pntd.0000775, PMID 20689820.
  - Not endemic (Discussion): "non-endemic areas such as Taiwan"
  - Imported cases (Abstract, Conclusions): "imported dengue cases are able to initiate indigenous epidemics"
  - Southern concentration (Results, 1998–2007): "98.45% (9,756/9,910) of total confirmed indigenous cases in Taiwan"
  - Study areas (Methods): "three epidemic areas in Southern Taiwan [Tainan (TN), Kaohsiung (KH), and Pingtung (PT)]"
  - URLs: https://doi.org/10.1371/journal.pntd.0000775 ; full text read at https://europepmc.org/article/PMC/PMC2914757
