# Week 4 Assignment — Three Roads: Choose Your Stack with AI

## 📋 1. The Four Personal Constraints

1. **Constraint 1: Budget (100% Free Only)**
   - Zero hosting, domain, or database subscription fees. Must utilize reliable free-tier infrastructure.

2. **Constraint 2: Honest Skill Level**
   - Intermediate Python Backend Engineer. Highly proficient in Python 3.10+, FastAPI, Flask, SQL, Docker, and REST API architecture; basic proficiency in HTML5/CSS3. I do not want to spend 30+ hours fighting complex JavaScript frontend frameworks, hydration bugs, or SPA state bundlers.

3. **Constraint 3: Portfolio Needs (Sitemap & Content Map)**
   - Must showcase 4 core backend projects:
     - **Task 4:** FastAPI + Supabase Auth IdP (JWT Bearer middleware & Swagger UI)
     - **Task 2:** Docker Compose + PostgreSQL B-tree indexing (`EXPLAIN ANALYZE` 0.526 ms ➔ 0.054 ms ~10x speedup) + Redis 7 cache
     - **Task 3:** SQLite CRUD API + raw SQL parameterized queries (`tasks.db`)
     - **Task 1:** Flask microservice + UTC ISO 8601 status API
   - Must display custom SVG graphics (`hero_banner.svg`, `favicon.svg`), code snippets, benchmark tables, and direct links to public GitHub repositories.

4. **Constraint 4: Work Display & Backend Requirement**
   - *Display Format:* Code repository links, benchmark performance cards, text case studies, and interactive OpenAPI Swagger `/docs` links.
   - *Dynamic Backend Requirement:* **Not yet for the portfolio site itself.** The portfolio site should be a lightning-fast, zero-maintenance static site. Live backend API demos are hosted separately on free-tier Render/Supabase.

---

## 🚦 2. The Three Stack Options (Simplest ➔ Most Powerful)

### Road 1: Simplest — Vanilla HTML5 / Modern CSS / Vanilla JS
* **How I'd Build:** Semantic HTML5 pages, CSS custom properties (matching Week 3 Identity Kit tokens `#0F172A`, `#10B981`, `Inter`, `JetBrains Mono`), zero build tools or npm bundler setup.
* **Where I'd Host (Free):** GitHub Pages (100% Free).
* **Needs Backend for Portfolio Site?** No (Static site).
* **Real Trade-off:** Extremely fast to construct (< 2 hours), 100/100 Lighthouse performance, zero build pipeline failures, but requires manual HTML duplicating if the portfolio scales beyond 10+ pages in the future.

---

### Road 2: Moderate — Vite + React + Tailwind CSS
* **How I'd Build:** Modular React components (Hero, CaseStudyCard, BenchmarkTable) styled with Tailwind CSS utility classes and bundled via Vite.
* **Where I'd Host (Free):** Vercel or Netlify Free Tier.
* **Needs Backend for Portfolio Site?** No (Static Single-Page Application).
* **Real Trade-off:** Reusable component architecture and clean state management, but introduces `node_modules` dependency bloat, build pipeline configuration overhead, and Tailwind setup time.

---

### Road 3: Most Powerful — Next.js App Router + Tailwind CSS + Framer Motion
* **How I'd Build:** Full-stack React SSR framework utilizing Next.js App Router, server-side rendering, and Framer Motion micro-animations.
* **Where I'd Host (Free):** Vercel Free Tier.
* **Needs Backend for Portfolio Site?** Optional (Node.js API routes built-in).
* **Real Trade-off:** Industrial-grade SSR, automatic route generation, and dynamic rendering, but high maintenance complexity, cold start latency risks, package deprecation debt, and a steep learning curve for a backend-focused engineer.

---

## 🔬 3. Pressure-Testing the Front-Runner

| Pressure Test Question | Road 1 (Simplest: Vanilla HTML/CSS) | Road 3 (Most Powerful: Next.js) |
| :--- | :--- | :--- |
| **What breaks if I pick this?** | Nothing breaks. HTML/CSS is native to every browser and never goes out of date. | Build step can break on npm updates, hydration mismatches, or missing node APIs. |
| **What do I maintain long-term?** | Zero framework maintenance. Just raw HTML text and CSS tokens. | Weekly `npm update` packages, framework breaking changes, and Vercel build logs. |
| **Can I finish in 2 weeks?** | **Yes (1 day).** Leaves 13 days to polish backend APIs and write technical docs. | High risk. 10+ days spent debugging React components and layout shifts. |
| **Does it show my work well?** | **Yes.** Clean typography, SVG vector graphics, benchmark tables, and code snippets render perfectly. | Yes, but the complex frontend code distracts from my actual Python backend work. |

---

## 🎯 4. Decision & Rationale (In My Own Words)

### Chosen Stack: **Road 1 — Vanilla HTML5 / Modern CSS on GitHub Pages**

### Why I Chose Road 1 & Rejected Roads 2 & 3:

> "As a Python Backend AI Engineer, my primary value is code architecture, PostgreSQL database indexing, API security, and containerization—not complex frontend React state management. 
> 
> I explicitly chose **Road 1 (Vanilla HTML5/CSS on GitHub Pages)** because it is 100% free, loads instantaneously (< 100ms), requires zero build tools, and never breaks due to npm dependency drift. Can I maintain this? Absolutely—editing an HTML file takes seconds without compiling code. Does it show my work well? Yes—it displays my benchmark numbers, terminal SVG graphics, and GitHub repo links with extreme clarity.
> 
> I rejected **Road 2 (Vite + React)** and **Road 3 (Next.js)** because spending 20 hours configuring JavaScript bundlers, Tailwind configs, and React hooks is an unnecessary distraction. For the question of whether the portfolio site needs a backend, I honestly answer: **not yet**. The portfolio website itself should remain a crisp static page, while linking out to my real live backend services running on Render and Supabase."
