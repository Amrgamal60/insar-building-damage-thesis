# Literature search, November 2026: common brief for every theme

## The study (design facts only)

A Master's thesis asks: does satellite InSAR ground motion measured BEFORE building damage improve the held-out
prediction of WHERE that damage is recorded, beyond a baseline without InSAR (building, soil, terrain, location)?

Three designs exist:
1. A discovery city: about 60 building-collapse events in 3 years, located only to street level (median location
   uncertainty about 130 m), analysed on 250 m cells (a few hundred cells, about 30 positive). Sentinel-1 velocity
   (LiCSAR/LiCSBAS, about 100 m) that overlaps the event period, so not strictly "before".
2. A US city: about 65 dated collapse events, OPERA DISP-S1 displacement (30 m), 250 m cells, 1-year window before
   each event.
3. A US city on expansive clay: about 2,800 dated foundation-repair permits on about 150,000 detached houses,
   OPERA DISP-S1 (30 m, one ascending track, line of sight only), trend velocity over the 24 months before each
   event; nested case-control (50 controls per case); logistic regression; 5-fold spatially blocked cross-validation
   (2 km blocks); test statistic = change in out-of-fold average precision when velocity is added; null = 999
   variogram-matched surrogate fields, conditional on the baseline features; plus an area-level Poisson panel with
   cell and quarter fixed effects; a remodel-permit negative control.

A new preregistered test is being planned. We want to know which published methods could make such a design
stronger, what limitations their authors state, and what data each method needs.

## What to return for every paper

| Field | Rule |
|---|---|
| Citation | Authors, year, title, journal, DOI |
| DOI check | Query `https://api.crossref.org/works/<DOI>` and confirm title, journal and year. Write VERIFIED or UNVERIFIED |
| Venue | Scimago quartile (Q1/Q2) LOOKED UP, with the source, year and subject category; or "IEEE journal". Never recall a quartile from memory. If you cannot look it up, write "quartile not verified" |
| Read depth | full text / abstract only / secondary source |
| What it does | Problem, data, method, validation design (held-out? spatially blocked? baseline without InSAR? motion before the outcome?) |
| Limitations | As the authors state them. Quote (25 words or fewer) or paraphrase, and say where in the paper. Add your own only under a separate label |
| Data the method needs | Resolution, time series or velocity only, number of events, location precision, two geometries, etc. |
| Use for us | Which of the three designs could use it, and what would be needed. Do not judge whether it "raises power" |

## Rules

- Venue filter: Scimago Q1 or Q2 journals, or IEEE journals/transactions/letters. Conference papers (including IEEE
  IGARSS), preprints, theses, abstracts and vendor pages go in a separate list "Found, outside the venue filter".
- Papers you found but could not read go in "Identified, not read".
- "Nothing found" is a valid answer for any sub-question. Never invent a paper, a DOI, a quartile or a limitation.
- Aim for 12 to 20 papers that pass the filter, most recent first within each sub-question, 2015 or later unless a
  paper is the standard reference for a method.
- Tools: web search and web fetch (load them with ToolSearch if they are deferred); `curl` to
  `https://api.openalex.org/works?search=<query>&per-page=25` (citing papers: `filter=cites:<OpenAlex id>`),
  `https://api.crossref.org/works/<DOI>`, `https://api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=title,abstract`.
  OpenAlex's `open_access.oa_url` gives open full texts.
- Privacy: put no e-mail address, name or project detail in any request (no `mailto=`, no e-mail in a User-Agent).
  Use only generic topic words in search queries.
- Do not bypass access controls or anti-bot pages. If a site refuses, use another source and say so.
- Write ONLY the output file named in your task. Do not edit any other file. Do not download large files.
- Write in plain English. No em dashes.
- Finish with a reply of 200 words or fewer: how many papers passed, the three most useful methods, and the file path.

## Already assessed (do not repeat; cite only if a new point needs them)

Burnol 2021; te Brake 2013; Scoular 2019; Toure 2025; Jiang 2023; Liu 2022; Qiao 2023; Miller and Shirzaei 2019;
Welch 2024; Peduto 2019 (Soils and Foundations); Nicodemo 2020; Ezquerro 2020; Del Soldato 2019; Drougkas 2020;
Milillo 2018; Giardina 2018; Harrison 2012; Barthelemy 2024; Kaveh 2007; Hudak 1998; Williams 2003, 2008;
Yang 2026 (Remote Sensing of Environment, Kunming); Ma 2022 (IJAEOG); Sadhasivam 2025 (Nature Sustainability);
Ohenhen 2025 (Nature Cities, 28 US cities); Fouad 2025 (Earth's Future, Alexandria); Mohamadi 2020 (Remote Sensing,
Alexandria); Tay 2022 (Nature Sustainability).
