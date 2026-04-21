#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import json
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA_FILE = BASE / "src" / "data" / "trending.json"
ZH_DIR = BASE / "src" / "pages" / "zh" / "trending"
EN_DIR = BASE / "src" / "pages" / "en" / "trending"
TMP_HTML = Path("/tmp/trending.html")


def run_curl() -> str:
    cmd = [
        "curl",
        "-s",
        "--connect-timeout",
        "10",
        "--max-time",
        "20",
        "https://github.com/trending",
        "-H",
        "User-Agent: Mozilla/5.0",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        raise RuntimeError(f"curl failed: {p.stderr.strip()}")
    TMP_HTML.write_text(p.stdout, encoding="utf-8")
    return p.stdout


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_repos(page: str):
    rows = re.findall(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', page, flags=re.S)
    repos = []
    for row in rows[:10]:
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="(/[^"]+)"', row, flags=re.S)
        href = m.group(1).strip("/") if m else "unknown/unknown"
        name = href
        url = f"https://github.com/{href}"

        m = re.search(r'<p[^>]*class="[^"]*color-fg-muted[^"]*"[^>]*>(.*?)</p>', row, flags=re.S)
        desc = strip_tags(m.group(1)) if m else ""

        m = re.search(r'itemprop="programmingLanguage"[^>]*>(.*?)<', row, flags=re.S)
        lang = strip_tags(m.group(1)) if m else "Unknown"

        m = re.search(rf'href="/{re.escape(href)}/stargazers"[^>]*>(.*?)</a>', row, flags=re.S)
        if m:
            star_text = strip_tags(m.group(1))
            mm = re.search(r'([\d,]+)', star_text)
            total = mm.group(1) if mm else "?"
        else:
            total = "?"

        m = re.search(r'([\d,]+)\s*stars\s*(today|this week)', row, flags=re.S)
        today = m.group(1) if m else "?"

        repos.append(
            {
                "name": name,
                "url": url,
                "desc": desc,
                "lang": lang,
                "total": total,
                "today": today,
            }
        )
    if len(repos) < 5:
        raise RuntimeError("parsed repos too few; github page structure may have changed")
    return repos


def rank_label(i: int) -> str:
    return ["🥇 1", "🥈 2", "🥉 3"][i] if i < 3 else f"#{i+1}"


def fmt_cn_date(d: dt.date) -> str:
    return f"{d.year}年{d.month}月{d.day}日"


def fmt_en_date(d: dt.date) -> str:
    return d.strftime("%b %d, %Y")


def zh_title(d: dt.date, repos):
    top = repos[0]
    return f"GitHub 今日热榜 Top 10（{fmt_cn_date(d)}）— {top['name']} 领跑 +{top['today']}⭐"


def en_title(d: dt.date, repos):
    top = repos[0]
    return f"GitHub Trending Top 10 ({fmt_en_date(d)}) — {top['name']} Leads"


def zh_summary(repos):
    a, b = repos[0], repos[1]
    return f"{a['name']} 今日 +{a['today']} 居首，{b['name']} 等项目持续走强，覆盖 AI 与开发工具热点。"


def en_summary(repos):
    a, b = repos[0], repos[1]
    return f"{a['name']} leads with +{a['today']} today, followed by {b['name']} and other strong AI/dev-tool signals."


def astro_page(lang: str, date_str: str, d: dt.date, repos):
    if lang == "zh":
        title = zh_title(d, repos)
        desc = f"{date_str} GitHub Trending 每日精选，Top 10 开源项目速览与解读。"
        h1 = f"GitHub 今日热榜 Top 10（{fmt_cn_date(d)}）"
        intro = "每日追踪 GitHub Trending Top 10，聚焦 AI、开发工具与高增长项目。"
        summary_title = "📊 今日总结"
        takeaways = [
            f"🔥 榜首项目：{repos[0]['name']}（今日 +{repos[0]['today']}）",
            f"⚡ 第二名：{repos[1]['name']}（今日 +{repos[1]['today']}）",
            "🧭 今日榜单覆盖 AI、基础设施、效率工具等方向",
        ]
        follow = "关注 GitHubCool，每日为你追踪 GitHub 最新趋势！🚀"
        tag = "🔥 热榜"
    else:
        title = en_title(d, repos)
        desc = f"Daily GitHub Trending Top 10 for {date_str}, with concise analysis and highlights."
        h1 = f"GitHub Trending Top 10 ({fmt_en_date(d)})"
        intro = "Daily GitHub Trending Top 10, focused on AI, dev tools, and high-growth open-source projects."
        summary_title = "📊 Today's Takeaways"
        takeaways = [
            f"🔥 #1 project: {repos[0]['name']} (+{repos[0]['today']} today)",
            f"⚡ #2 project: {repos[1]['name']} (+{repos[1]['today']} today)",
            "🧭 The list spans AI, infra, and developer productivity tooling",
        ]
        follow = "Follow GitHubCool for daily GitHub trending insights! 🚀"
        tag = "🔥 Trending"

    repos_js = json.dumps(repos, ensure_ascii=False, indent=2)
    takeaways_js = json.dumps(takeaways, ensure_ascii=False)

    return f'''---
import Base from '../../../layouts/Base.astro';

const repos = {repos_js};
const takeaways = {takeaways_js};

function rankLabel(i: number) {{
  return i === 0 ? '🥇 1' : i === 1 ? '🥈 2' : i === 2 ? '🥉 3' : `#${{i + 1}}`;
}}
---
<Base title="{title}" description="{desc}">

<article class="post">
  <header>
    <span class="tag">{tag}</span>
    <h1>{h1}</h1>
    <p class="meta">📅 {date_str} · ✍️ GitHubCool · 🏷️ GitHub Trending, Open Source</p>
  </header>

  <section class="intro">
    <p>{intro}</p>
  </section>

  <section class="repo-list">
    {{repos.map((repo, i) => (
      <div class={{`repo-card ${{i < 3 ? 'top3' : ''}}`}}>
        <div class="rank">{{rankLabel(i)}}</div>
        <h2><a href={{repo.url}} target="_blank">{{repo.name}}</a></h2>
        <p class="stars">⭐ {{repo.total}} total | +{{repo.today}} today | {{repo.lang}}</p>
        <p>{{repo.desc || 'No description provided.'}}</p>
      </div>
    ))}}
  </section>

  <section class="summary">
    <h2>{summary_title}</h2>
    <ul>
      {{takeaways.map((line) => <li>{{line}}</li>)}}
    </ul>
    <p>{follow}</p>
  </section>
</article>

</Base>

<style>
  .post {{ max-width: 800px; margin: 0 auto; }}
  .post header {{ text-align: center; margin-bottom: 2rem; }}
  .post h1 {{ font-size: 2rem; margin: 1rem 0; line-height: 1.4; }}
  .meta {{ color: var(--text-muted); font-size: 0.9rem; }}
  .intro {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; }}
  .repo-list {{ display: flex; flex-direction: column; gap: 1rem; }}
  .repo-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem; transition: border-color 0.2s; }}
  .repo-card:hover {{ border-color: var(--accent); }}
  .repo-card.top3 {{ border-left: 3px solid var(--accent); }}
  .rank {{ font-size: 1.35rem; font-weight: 700; margin-bottom: 0.4rem; }}
  .repo-card h2 {{ font-size: 1.1rem; margin-bottom: 0.4rem; }}
  .repo-card h2 a {{ text-decoration: none; }}
  .stars {{ color: var(--accent-orange); font-size: 0.9rem; margin-bottom: 0.6rem; }}
  .summary {{ margin-top: 2rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
  .summary ul {{ list-style: none; display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.8rem; }}
  .tag {{ display: inline-block; background: rgba(248,81,73,0.15); color: var(--accent-red); padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; }}
</style>
'''


def update_archive(data, lang: str, entry: dict):
    posts = data.get(lang, [])
    posts = [p for p in posts if p.get("date") != entry["date"]]
    posts.insert(0, entry)
    data[lang] = posts


def main():
    parser = argparse.ArgumentParser(description="Generate daily GitHub trending pages and update archive data.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD. Default: today (local)")
    args = parser.parse_args()

    if args.date:
      d = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
      d = dt.date.today()
    date_str = d.isoformat()

    html_page = run_curl()
    repos = parse_repos(html_page)

    zh_file = ZH_DIR / f"{date_str}.astro"
    en_file = EN_DIR / f"{date_str}.astro"
    zh_file.write_text(astro_page("zh", date_str, d, repos), encoding="utf-8")
    en_file.write_text(astro_page("en", date_str, d, repos), encoding="utf-8")

    if DATA_FILE.exists():
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    else:
        data = {"zh": [], "en": []}

    zh_entry = {
        "date": date_str,
        "title": zh_title(d, repos),
        "summary": zh_summary(repos),
        "href": f"/GitHubCool/zh/trending/{date_str}/",
    }
    en_entry = {
        "date": date_str,
        "title": en_title(d, repos),
        "summary": en_summary(repos),
        "href": f"/GitHubCool/en/trending/{date_str}/",
    }

    update_archive(data, "zh", zh_entry)
    update_archive(data, "en", en_entry)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Generated: {zh_file.relative_to(BASE)}")
    print(f"Generated: {en_file.relative_to(BASE)}")
    print(f"Updated: {DATA_FILE.relative_to(BASE)}")


if __name__ == "__main__":
    main()
