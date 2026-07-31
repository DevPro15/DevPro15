#!/usr/bin/env python3
"""
Self-contained GitHub stats card generator for DevPro15.
No third-party libraries, no forks, no external services — stdlib only.
Fetches your public stats via the GitHub GraphQL API and renders three themed
SVG cards (stats, top languages, streak) that match the profile banner palette.

Run by .github/workflows/stats.yml on a schedule. Set MOCK=1 to render sample
cards locally without hitting the API.
"""
import os, json, sys, html, datetime, urllib.request

USER  = os.environ.get("GH_USER", "DevPro15")
TOKEN = os.environ.get("GH_TOKEN", "")
MOCK  = os.environ.get("MOCK", "") == "1"
OUT   = os.environ.get("OUT_DIR", "assets")

# ---- palette (matches banner) ----
BG      = "#0A101F"
BORDER  = "#1B2740"
TITLE   = "#22D3EE"
ACCENT  = "#A78BFA"
GREEN   = "#10B981"
LABEL   = "#94A3B8"
VALUE   = "#F8FAFC"
RING_BG = "#22304d"
FONT    = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"

LANG_COLORS = {
    "JavaScript":"#F1E05A","TypeScript":"#3178C6","HTML":"#E34C26","CSS":"#563D7C",
    "Python":"#3572A5","Java":"#B07219","PHP":"#4F5D95","C++":"#F34B7D","C":"#555555",
    "C#":"#178600","Go":"#00ADD8","Ruby":"#701516","Shell":"#89E051","Vue":"#41B883",
    "Dart":"#00B4AB","Kotlin":"#A97BFF","Rust":"#DEA584","Swift":"#F05138","SCSS":"#C6538C",
    "Jupyter Notebook":"#DA5B0B","EJS":"#A91E50","Blade":"#F7523F","Astro":"#FF5A03",
}
def lang_color(n): return LANG_COLORS.get(n, ACCENT)

# ─────────────────────────── data ───────────────────────────
def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": USER},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]

def fetch():
    prof = gql("""
      query($login:String!){
        user(login:$login){
          createdAt
          followers{totalCount}
          repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
            totalCount
            nodes{ stargazerCount
              languages(first:10, orderBy:{field:SIZE, direction:DESC}){
                edges{ size node{ name } } } }
          }
        }
      }""", {"login": USER})["user"]

    stars = sum(n["stargazerCount"] for n in prof["repositories"]["nodes"])
    langs = {}
    for n in prof["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]

    created = int(prof["createdAt"][:4])
    now = datetime.datetime.utcnow()
    days = {}   # date -> count
    commits = prs = issues = reviews = 0
    for yr in range(created, now.year + 1):
        frm = f"{yr}-01-01T00:00:00Z"
        to  = f"{yr}-12-31T23:59:59Z" if yr < now.year else now.strftime("%Y-%m-%dT%H:%M:%SZ")
        cc = gql("""
          query($login:String!,$from:DateTime!,$to:DateTime!){
            user(login:$login){ contributionsCollection(from:$from,to:$to){
              totalCommitContributions totalPullRequestContributions
              totalIssueContributions totalPullRequestReviewContributions
              contributionCalendar{ weeks{ contributionDays{ date contributionCount } } }
            }}}""", {"login": USER, "from": frm, "to": to})["user"]["contributionsCollection"]
        commits += cc["totalCommitContributions"]
        prs     += cc["totalPullRequestContributions"]
        issues  += cc["totalIssueContributions"]
        reviews += cc["totalPullRequestReviewContributions"]
        for w in cc["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    total_contrib, cur, longest, cur_range, long_range = streaks(days)
    return dict(user=USER, stars=stars, commits=commits, prs=prs, issues=issues,
                reviews=reviews, followers=prof["followers"]["totalCount"],
                repos=prof["repositories"]["totalCount"], langs=langs,
                total_contrib=total_contrib, cur_streak=cur, long_streak=longest,
                cur_range=cur_range, long_range=long_range,
                since=f"{created}")

def streaks(days):
    if not days:
        return 0, 0, 0, "", ""
    items = sorted(days.items())
    total = sum(c for _, c in items)
    # longest
    longest = cur = 0
    ls = le = cs = None
    best_s = best_e = None
    prev = None
    for date, c in items:
        if c > 0:
            if cur == 0: cs = date
            cur += 1
            ce = date
            if cur > longest:
                longest = cur; best_s, best_e = cs, ce
        else:
            cur = 0
    # current streak (walk back from last day)
    curr = 0; cstart = cend = None
    for date, c in reversed(items):
        if c > 0:
            curr += 1; cstart = date
            if cend is None: cend = date
        else:
            # allow today to be 0 without breaking (streak counts up to yesterday)
            if cend is None:
                continue
            break
    def fmt(a, b):
        if not a: return ""
        fa = datetime.date.fromisoformat(a).strftime("%b %d")
        fb = datetime.date.fromisoformat(b).strftime("%b %d, %Y")
        return f"{fa} – {fb}"
    return total, curr, longest, fmt(cstart, cend), fmt(best_s, best_e)

def mock():
    return dict(user=USER, stars=128, commits=1342, prs=57, issues=39, reviews=21,
                followers=64, repos=41,
                langs={"JavaScript":52000,"TypeScript":31000,"HTML":18000,"CSS":15000,
                       "PHP":9000,"Python":6000,"Blade":4200,"EJS":2600},
                total_contrib=2874, cur_streak=17, long_streak=43,
                cur_range="Jul 15 – Jul 31, 2026", long_range="Mar 02 – Apr 13, 2026",
                since="2021")

# ─────────────────────────── render ───────────────────────────
def esc(s): return html.escape(str(s), quote=True)

def card(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{FONT}">'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{BG}" '
            f'stroke="{BORDER}" stroke-width="1.5"/>{body}</svg>')

def kfmt(n):
    return f"{n/1000:.1f}k".replace(".0k","k") if n >= 1000 else str(n)

def render_stats(d):
    w, h = 500, 210
    rows = [("★","Total Stars Earned", d["stars"]),
            ("◒","Total Commits","{}".format(d["commits"])),
            ("⇄","Total PRs", d["prs"]),
            ("◍","Total Issues", d["issues"]),
            ("✓","Pull Requests Reviewed", d["reviews"]),
            ("♦","Followers", d["followers"])]
    b = [f'<text x="26" y="42" font-size="18" font-weight="700" fill="{TITLE}" '
         f'letter-spacing="0.5">{esc(d["user"])}’s GitHub Stats</text>',
         f'<line x1="26" y1="54" x2="180" y2="54" stroke="{ACCENT}" stroke-width="2"/>']
    y = 84
    for icon, label, val in rows:
        b.append(f'<text x="30" y="{y}" font-size="14" fill="{ACCENT}">{esc(icon)}</text>')
        b.append(f'<text x="52" y="{y}" font-size="14" fill="{LABEL}">{esc(label)}</text>')
        b.append(f'<text x="{w-26}" y="{y}" font-size="15" font-weight="700" '
                 f'fill="{VALUE}" text-anchor="end">{esc(val)}</text>')
        y += 21
    return card(w, h, "".join(b))

def render_langs(d):
    w, h = 500, 210
    items = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:6]
    tot = sum(v for _, v in items) or 1
    b = [f'<text x="26" y="42" font-size="18" font-weight="700" fill="{TITLE}">Most Used Languages</text>',
         f'<line x1="26" y1="54" x2="230" y2="54" stroke="{ACCENT}" stroke-width="2"/>']
    y = 78
    barx, barw = 150, w - 150 - 70
    for name, size in items:
        pct = size / tot * 100
        col = lang_color(name)
        b.append(f'<circle cx="32" cy="{y-4}" r="5" fill="{col}"/>')
        b.append(f'<text x="46" y="{y}" font-size="13.5" fill="{LABEL}">{esc(name)}</text>')
        b.append(f'<rect x="{barx}" y="{y-11}" width="{barw}" height="9" rx="4.5" fill="{RING_BG}"/>')
        b.append(f'<rect x="{barx}" y="{y-11}" width="{barw*pct/100:.1f}" height="9" rx="4.5" fill="{col}"/>')
        b.append(f'<text x="{w-26}" y="{y}" font-size="13" font-weight="700" fill="{VALUE}" '
                 f'text-anchor="end">{pct:.1f}%</text>')
        y += 22
    return card(w, h, "".join(b))

def render_streak(d):
    w, h = 1180, 200
    cx = [w*0.19, w*0.5, w*0.81]
    import math
    def num(x, val, sub1, sub2, color, ring=False):
        s = []
        if ring:
            r = 47
            s.append(f'<circle cx="{x}" cy="80" r="{r}" fill="none" stroke="{RING_BG}" stroke-width="6"/>')
            s.append(f'<circle cx="{x}" cy="80" r="{r}" fill="none" stroke="{color}" stroke-width="6" '
                     f'stroke-linecap="round" stroke-dasharray="{2*math.pi*r*0.82:.1f} 999" '
                     f'transform="rotate(-90 {x} 80)"/>')
            s.append(f'<text x="{x}" y="90" font-size="34" font-weight="800" fill="{VALUE}" text-anchor="middle">{val}</text>')
        else:
            s.append(f'<text x="{x}" y="94" font-size="42" font-weight="800" fill="{color}" text-anchor="middle">{val}</text>')
        s.append(f'<text x="{x}" y="152" font-size="14" fill="{LABEL}" text-anchor="middle" letter-spacing="1">{esc(sub1)}</text>')
        s.append(f'<text x="{x}" y="173" font-size="11.5" fill="#64748B" text-anchor="middle">{esc(sub2)}</text>')
        return "".join(s)
    b = [num(cx[0], d["total_contrib"], "Total Contributions", d["since"]+" – Present", TITLE),
         num(cx[1], d["cur_streak"], "Current Streak", d["cur_range"], GREEN, ring=True),
         num(cx[2], d["long_streak"], "Longest Streak", d["long_range"], ACCENT)]
    for xd in (w*0.345, w*0.655):
        b.append(f'<line x1="{xd}" y1="40" x2="{xd}" y2="172" stroke="{BORDER}" stroke-width="1.4"/>')
    return card(w, h, "".join(b))

def main():
    os.makedirs(OUT, exist_ok=True)
    d = mock() if MOCK else fetch()
    open(f"{OUT}/stats.svg", "w").write(render_stats(d))
    open(f"{OUT}/top-langs.svg", "w").write(render_langs(d))
    open(f"{OUT}/streak.svg", "w").write(render_streak(d))
    print("wrote cards:", d["stars"], "stars,", d["commits"], "commits,",
          d["cur_streak"], "day streak")

if __name__ == "__main__":
    main()
