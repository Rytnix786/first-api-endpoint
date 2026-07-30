# Week 3 Assignment — Personal Identity Kit

## ✒️ 1. Typography Selection
- **Heading Font:** `Inter` (Clean, geometric, modern sans-serif for high legibility)
- **Body & Code Font:** `JetBrains Mono` (Technical, precise monospace for code and metrics)

---

## 🎨 2. Color Palette (Tight 4-Color System)

| Color Role | Hex Code | Color Preview | Description |
| :--- | :--- | :--- | :--- |
| **Near-White Background** | `#F8FAFC` | `Slate 50` | Clean, crisp, neutral surface background |
| **Near-Black Text** | `#0F172A` | `Slate 900` | High-contrast, sharp typography color |
| **Muted UI / Borders** | `#64748B` | `Slate 500` | Calm secondary text, grid lines, and metadata |
| **Primary Accent** | `#10B981` | `Emerald 500` | Terminal green indicator (signals status: ok & performance) |

---

## 🏷️ 3. Logo & Monogram

### Monogram Concept
A minimal backend terminal prompt combined with initial **R**:
> `R >_`

### SVG Logo File
- **Path:** `AI-Fluency-w3/favicon.svg`
- **Design:** Dark slate rounded container (`#0F172A`), emerald prompt glyph (`#10B981`), and bold white monogram (`#F8FAFC`).

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect width="512" height="512" rx="112" fill="#0F172A"/>
  <path d="M 140 180 L 210 256 L 140 332" fill="none" stroke="#10B981" stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="240" y="320" font-family="JetBrains Mono, Inter, sans-serif" font-weight="800" font-size="190" fill="#F8FAFC">R</text>
  <circle cx="410" cy="315" r="22" fill="#10B981"/>
</svg>
```

---

## 📝 4. Standing Two-Line Style Note (For Claude Project Instructions)

```text
Identity: Fonts are Inter (Headings) and JetBrains Mono (Body/Code). Palette is #F8FAFC (Bg), #0F172A (Text), #64748B (Muted), #10B981 (Emerald Accent).
Mood: Crisp, precise, developer-first minimalist aesthetic where the code and performance benchmarks are the loudest elements on the page.
```
