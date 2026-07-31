# DevPro15 profile — setup checklist

Your new animated profile is assembled. `README.md` has been replaced (old one saved as
`README.old.md`). Work through these by-hand steps in order.

## 1. Files are in place ✅ (done for you)
- `dark.svg` and `light.svg` — the animated banner, at the repo root
- `assets/stats.svg`, `assets/top-langs.svg`, `assets/streak.svg` — your stats cards (placeholder
  numbers for now; the Action fills real ones on first run)
- `.github/scripts/gen_cards.py` — your own stats-card generator (stdlib Python, no dependencies)
- `.github/workflows/stats.yml` — regenerates the cards daily
- `.github/workflows/snake.yml` — the contribution-snake workflow
- `README.md` — banner + stats + snake + badges, wired to `DevPro15/DevPro15`

Commit and push all of this to `main`.

## 2. Stats cards — 100% yours, no forks (~0 min)
There is **nothing to fork and no Vercel to set up.** The three cards are generated *inside your own
repo* by `.github/workflows/stats.yml`, which runs `gen_cards.py`, pulls your numbers from the GitHub
API, and commits refreshed SVGs. It runs daily and on every push, and you can trigger it anytime:
Actions → **Generate Stats Cards** → Run workflow.

- The workflow uses the built-in `GITHUB_TOKEN` — no secrets to configure.
- Want **private** contributions counted too? Create a classic token (repo scope), add it as a repo
  secret, and change `GH_TOKEN` in `stats.yml` from `secrets.GITHUB_TOKEN` to your secret name.
- No rank/letter-grade is shown — it's weighted toward stars/followers and misleads newer accounts.
- Tweak colors, rows, or which stats appear by editing `gen_cards.py` (or tell me).

## 3. Turn on the snake
1. Repo → **Settings → Actions → General → Workflow permissions → Read and write → Save.**
   (This is the *repo's* settings, not your account settings.)
2. The `snake.yml` push triggers the Action. Check the **Actions** tab — it should go green in
   ~1 min and create an `output` branch.
3. Once green, **uncomment the SNAKE block** in `README.md` (remove the `<!--` / `-->` around it).
   Don't uncomment it earlier — the `output` branch doesn't exist yet and the image shows broken.

It regenerates every 12 hours. Force it anytime: Actions → Generate Snake Animation → Run workflow.

## 4. Fix the placeholders in README.md
- **LinkedIn** — I guessed `linkedin.com/in/DevPro15`; point it at your real profile.
- **Email** — currently `zairabbas1533@outlook.com` (from your old README). Change if you'd rather
  use another address.
- **Portfolio** badge — links to `#`; set it when your portfolio is live.
- Same LinkedIn/portfolio values appear in the banner info panel — tell me and I'll regenerate the SVGs.

## 5. Cleanup (optional)
Leftover from the old profile, no longer referenced by the README: `devcard.svg`, `devcard.png`,
`gh-readme-header*.png`, `README.old.md`, and the old icons in `assets/` (`discord*`, `twitter*`,
`codesandbox*`). Delete whatever you don't want — but **keep** `assets/stats.svg`,
`assets/top-langs.svg`, and `assets/streak.svg`, they're your new cards.

---
### Notes
- Banner regenerates only when I rebuild it — the portrait is baked into the SVGs. The generator
  script and source data are kept so any field, color, or crop can be changed.
- If a change "doesn't show up," it's almost always CDN cache: open the raw SVG URL with `?v=999`
  appended and confirm the change is in the file; GitHub's CDN clears on its own in minutes–hours.
- Dark-mode assets only render in dark mode — switch your GitHub theme to test both.
