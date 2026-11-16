# Place or Placeholder?

**When satellite embeddings genuinely improve dengue forecasts.** This is Paper 1 of a two-part study.

It tests whether AlphaEarth satellite embeddings improve weekly district-level dengue forecasts, or only act as a district identifier. The design has three parts:
- embeddings time-aligned to year t−1
- location-only controls (district ID, coordinates, shuffled embeddings, smooth random fields, static snapshot)
- spatial, regional and cross-country hold-out tests across Brazil, Colombia, Peru and Taiwan (OpenDengue v1.3.1)

- Plan: `docs/plans/paper1_evaluation_plan.txt`
- Background research: `docs/research/`

Compute runs on the team GPU server. Run `source env.sh` there before anything else (it keeps the venv and all caches inside the project folder).
