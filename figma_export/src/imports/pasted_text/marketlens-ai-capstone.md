Introducing MarketLens AI — an AI-powered Market Research Assistant we developed as our MSc Business Analytics capstone at ESADE.
The problem we set out to solve was real: teams across industries waste enormous time gathering competitive intelligence. Consultants, investors, product managers, marketing leads — everyone needs fast, defensible market insights. Nobody has time to produce them the old way.
Here's what we built:
Competitive Positioning Map: Companies plotted on a price vs. perceived customer value matrix, synthesised automatically from public data and internal documents. No more building slides by hand.
Sentiment Analysis Engine — We ingested tens of thousands of customer reviews and ran semantic analysis to surface exactly what customers love, what frustrates them, and how your brand compares to competitors across every dimension.
Dimension-by-Dimension Benchmarking: The tool identifies what customers actually care about in your market, then scores your company and each competitor against those dimensions, turning qualitative noise into a structured, actionable grid.
AI-Synthesised Insights: Rather than dumping raw data, the assistant surfaces the three or four things that actually matter: the gap you can exploit, the risk you should hedge, the trend you are late to communicate.
We validated the tool on the airline industry, comparing LiftAir against Ryanair, Lufthansa, easyJet, British Airways and Wizz Air across 48,000 reviews and 14 industry documents. The output was a full competitive intelligence report in minutes. Insights that would have taken an analyst days.

Who can use this? Investors assessing a new sector before a deal. Marketing teams benchmarking brand perception. Strategy leads entering a new market. Consultants needing fast, credible client deliverables.

This project was built by four ESADE MSc Business Analytics students as part of our capstone. It was one of the most technically and strategically rewarding things we worked on. Thank you to our partners and professors for the challenge and the support throughout.
If you are curious about the methodology, the tech stack, or how something like this could apply to your industry, feel free to reach out.
#MarketResearch #AI #BusinessAnalytics #ESADE #MachineLearning #Capstone #CompetitiveIntelligence #NLP #StartupTools



Prototyping plan: 
Category
Details
What to Learn First
Data availability
Can you get real-time competitive signals at a viable cost? Review platforms, pricing APIs, and web traffic data often sit behind paywalls or rate limits.
Insight quality
Does the AI surface non-obvious insights, or just restate what a user finds in 10 minutes on Google? This is the core value question.
User workflow fit
Do users want a report, a dashboard, or a conversational agent? The answer changes the entire product architecture.
Datasets Needed
Voice of the customer
Trustpilot, Google Reviews, Glassdoor, App Store / Play Store, Reddit, Twitter/X, G2, Capterra.
Competitive signals
SimilarWeb / SEMrush (traffic, keywords), LinkedIn job postings, press releases via NewsAPI, patent filings.
Market structure
Crunchbase / PitchBook (funding, M&A), SEC filings, earnings call transcripts, Statista / IBISWorld reports.
Pricing & product
Scraped pricing pages, feature comparison sites, product changelogs, and retailer listing data.
Integration priority
Reviews → News → Pricing → Financials
Models Needed
Semantic understanding
Sentence embedding model (e.g., text-embedding-3-small, SBERT) to cluster reviews, find themes, and measure similarity between companies.
Aspect-based sentiment
Fine-tuned classifier or prompted LLM for dimension-level scoring — not just overall polarity.
Synthesis layer
Frontier LLM (GPT-4o, Claude) with a structured prompt to generate the so-what from quantitative outputs.
Architecture note
No training from scratch needed. Focus is on prompt engineering and RAG.
KPIs to Measure
Competitive position
Relative sentiment score, share of voice, price index vs. category average, perceived value rank.
Customer signals
Aspect scores per dimension, sentiment trend over time, top emerging complaint themes, top emerging praise themes.
Market dynamics
Competitor activity score, market growth signal (review volume growth), whitespace index (important dimensions where all players score poorly).
Fabrizio's Prototype Plan
Phase 1 — Define (Days 1–2)
Pick one vertical and one focal company. Define 5–6 dimensions. Write evaluation rubric for good vs. bad insights. Identify 3 test users.
Phase 2 — Build (Days 3–6)
Scrape 500–1,000 reviews per company. Run aspect-based sentiment via prompted LLM. Compute dimension scores. Generate 4–5 insights. Build static HTML output.
Phase 3 — Evaluate (Days 7–8)
Show output to 3 test users blind. Ask: is anything surprising? Would you act on this? What would you distrust? Score each insight as obvious / useful / wrong.
Phase 4 — Learn (Day 9)
Document what data was actually accessible, pipeline speed, where the LLM hallucinated, and whether users trusted the scores.
What will likely work
Dimension scoring and visual benchmarking — structured quantitative output from reviews is tractable and compelling.
What will likely not work
Synthesis insights will be too generic on first pass. Biggest failure mode is confident-sounding insights that just restate sentiment scores.
Key learning that matters
Whether users trust the output enough to act on it. Everything else is solvable with engineering time. Trust is the product.

Multipurpose: 
Audiences: 
Investors 
Companies themselves 
Customers 

Investors 
defensible moat? 
comparable companies margins? 


Companies 


what are the main complaints from customers? 
What are competitors doing that we aren't?
What is our pricing power? 
How is our social media presence vs competitors? 
Customers 




