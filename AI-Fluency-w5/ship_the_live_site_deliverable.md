# Week 5 Assignment — Ship the Live Site Deliverable

## 🌐 1. Live Public URLs & Sitemap Verification

* **Primary Live Portfolio URL:** [https://mehedi-hasan-llm.vercel.app/](https://mehedi-hasan-llm.vercel.app/)
* **Secondary GitHub Pages Mirror:** [https://rytnix786.github.io/first-api-endpoint/](https://rytnix786.github.io/first-api-endpoint/)
* **GitHub Repository:** [https://github.com/Rytnix786/first-api-endpoint](https://github.com/Rytnix786/first-api-endpoint)

### Sitemap Reachability Check:
- ✅ **Home / Hero Section:** Displays One-Line Claim (*"I build production-grade Python backend APIs..."*), Voice Card, and live green status badge.
- ✅ **Task 4 Case Study Card:** Opens [Task 4 FastAPI + Supabase Auth repository](https://github.com/Rytnix786/first-api-endpoint/tree/main/Task4-w4-a1).
- ✅ **Task 2 Case Study Card:** Opens [Task 2 Docker Compose + PostgreSQL Indexing repository](https://github.com/Rytnix786/first-api-endpoint/tree/main/Task2-w2).
- ✅ **Monogram SVG Logo (`R >_`):** Renders cleanly across all viewports without layout breaking.

---

## 👤 2. Real Person Review & Feedback Note

I shared the live portfolio URL with a **Senior Python Backend Engineer / Technical Peer** and asked for their candid reaction:

### Reviewer Reaction & Feedback:
> **What Landed Well:**
> *"The database benchmarking section is what immediately caught my eye. Seeing raw `EXPLAIN ANALYZE` execution timings dropping from `0.526 ms` to `0.054 ms` (~10x speedup) instantly proves you understand real-world database performance. The dark slate palette (`#0F172A`) and JetBrains Mono typography give it a legit developer terminal feel instead of a generic template."*
> 
> **What Confused or Needs Work:**
> *"The code benchmark cards are currently static JSON text blocks. It would be awesome if I could click a 'Run Live Benchmark' button directly on the website to trigger a live API call."*

---

## 🛠️ 3. The Honest "Still Ugly" List

Here are the 4 specific rough edges I am aware of and plan to improve in future iterations:

1. **Mobile Viewport Title Wrapping:** On smaller screens (e.g. iPhone SE 375px width), the long hero title wraps onto 4 lines, causing slight vertical padding compression.
2. **Static Benchmark Cards:** Benchmarks and query timings are displayed as static code blocks rather than interactive, live-updating WebSocket graphs.
3. **Hardcoded Dark Palette:** The site is hardcoded to `#0F172A` Slate Dark without a light/dark mode toggle switch.
4. **Manual Static Pagination:** Pages are duplicated manually in raw HTML rather than using a static site generator (SSG) like Astro or Next.js.

---

## 💡 4. How the Site is Built (No Mystery Code)

The entire portfolio site is built with **zero external build framework dependencies**:

* **HTML5 Semantic Structure (`index.html`):** Uses standard `<header>`, `<main>`, `<section>`, and `<footer>` elements for 100/100 screen reader accessibility.
* **CSS Custom Properties (`style.css`):** Employs CSS variables (`:root`) to define global identity kit tokens:
  - `--bg-color: #0F172A` (Slate Dark)
  - `--accent-emerald: #10B981` (Terminal Emerald Green)
  - `--font-heading: 'Inter', sans-serif`
  - `--font-code: 'JetBrains Mono', monospace`
* **SVG Vector Logo (`favicon.svg`):** Inline vector graphics drawn using native `<svg>`, `<rect>`, `<path>`, and `<text>` elements.
* **Automated Deployment (`.github/workflows/static.yml`):** Uses standard GitHub Actions to publish the root directory to GitHub Pages on every `git push origin main`.
