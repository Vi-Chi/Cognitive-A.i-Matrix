# PUBLIC_CHANNEL_MAP.md

## Primary Public Channels

| Channel | Purpose | Default Agent Action |
|---|---|---|
| GitHub README/docs | Canonical technical home | Prepare/update locally; push only if authorized. |
| GitHub Releases | Versioned milestones | Draft notes; publish only if authorized. |
| GitHub Pages / site | Public-facing landing/docs | Prepare static site; deploy only if authorized. |
| Google Drive public folder | Shareable docs/assets | Prepare sanitized copies; change sharing only if authorized. |
| Blog / Dev.to / Medium / Substack | Longer build logs | Draft posts; queue for review. |
| YouTube | Demos, build logs, explanations | Draft script/title/description/chapters. |
| Reddit / HN / forums | Feedback and collaborators | Draft community-specific posts; avoid spam. |
| Discord / Matrix / communities | Technical feedback | Draft concise update and question. |
| Hackaday / Instructables | Hardware build logs | Draft BOM, steps, safety notes, images list. |
| Zenodo / DOI archive | Stable release citation | Prepare metadata; publish only after review. |

## Channel Selection Rule

- Code maturity -> GitHub docs/release.
- Architecture maturity -> public architecture doc / blog.
- Hardware progress -> Hackaday/Instructables/YouTube.
- Research theory -> whitepaper/blog/Zenodo later.
- Need collaborators -> README + roadmap + community post.
- Need credibility -> tests, reproducible benchmarks, changelog, demo.
