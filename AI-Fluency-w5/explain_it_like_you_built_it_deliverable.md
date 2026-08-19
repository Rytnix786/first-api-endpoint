# Week 5 Assignment Deliverable — Explain It Like You Built It

**Student Name:** Mehedi Hasan  
**Live Portfolio URL:** [https://mehedi-hasan-llm.vercel.app/](https://mehedi-hasan-llm.vercel.app/)  
**GitHub Repository:** [https://github.com/Rytnix786/first-api-endpoint](https://github.com/Rytnix786/first-api-endpoint)  
**Track:** General AI Fluency — Week 5 (Build+ Phase)  

---

## 🎯 Chosen Piece of the Build:
**How my Next.js portfolio site automatically builds and updates across the world whenever I type `git push`, without me ever running a server on my laptop.**

---

## 💬 Plain-Words Explanation (As if Teaching a Friend):

> Imagine you wrote a recipe book on your computer, but instead of emailing a PDF to everyone every time you fix a typo, you have an automated publishing robot.
>
> That's basically how my live portfolio ([https://mehedi-hasan-llm.vercel.app/](https://mehedi-hasan-llm.vercel.app/)) works with **GitHub** and **Vercel**:
>
> 1. **The Code on My Machine:** When I edit my case studies (like adding my Nexus Researcher or MindStack systems), the raw code is written in React and TypeScript. Browsers can't read TypeScript directly.
> 2. **The Git Push (The Handshake):** When I'm done, I run `git push origin main`. GitHub receives the new files and immediately fires an automated signal (a "webhook") to Vercel saying: *"Hey, Mehedi just updated the main branch."*
> 3. **The Build Step (The Kitchen):** Vercel wakes up a fresh temporary cloud computer, downloads my repository, and runs `npm run build`. This step compresses all my images, compiles TypeScript into pure HTML/CSS/JavaScript, and minifies everything so the page loads in milliseconds.
> 4. **Edge Distribution (The Delivery):** Instead of storing the site on a single computer in one city, Vercel copies the newly built static files onto hundreds of servers worldwide (called Edge CDNs). So if someone opens my portfolio from Dhaka, London, or New York, the website is served from the closest data center to them instantly.
>
> The coolest thing I learned is that I don't need to keep my laptop turned on or rent an expensive server 24/7. The entire deployment pipeline takes under 40 seconds, gives me a zero-downtime update, and handles thousands of visitors automatically.
