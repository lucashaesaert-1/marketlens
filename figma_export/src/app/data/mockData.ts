export type Industry = "food-delivery" | "ride-sharing" | "saas" | "crm";
export type Audience = "investors" | "companies" | "customers";

export interface Company {
  id: string;
  name: string;
  price: number; // 1-10 scale
  perceivedValue: number; // 1-10 scale
  overallSentiment: number; // -1 to 1
  reviewCount: number;
  color: string;
}

export interface Dimension {
  name: string;
  importance: number; // 0-100
  scores: Record<string, number>; // company id -> score (0-100)
}

export interface SentimentTrend {
  month: string;
  [companyId: string]: number | string;
}

export interface Insight {
  type: "opportunity" | "risk" | "trend";
  title: string;
  description: string;
  impact: "high" | "medium" | "low";
  metrics?: string[];
  /** pipeline = default analysis; chat = from onboarding/dashboard conversation */
  source?: "pipeline" | "chat";
}

export interface PraiseComplaintTheme {
  company: string;
  companyId: string;
  praise: number;
  complaint: number;
}

export interface ShareOfVoiceItem {
  name: string;
  size: number;
  value: number;
}

export interface ChurnFlow {
  source: string;
  target: string;
  value: number;
}

export interface DimensionDelta {
  dimension: string;
  company: string;
  companyId: string;
  score: number;
  benchmark: number;
  delta: number;
}

export interface NewsHeadline {
  title: string;
  source: string;
  date: string;
  snippet: string;
  sentiment_hint: "positive" | "negative" | "neutral";
}

export interface StockDataPoint {
  date: string;
  close: number;
  adjusted_close: number;
}

export interface FinanceQuote {
  ticker: string;
  price: number | null;
  currency: string;
  change: number | null;
  pct_change: number | null;
  monthly_series?: StockDataPoint[];
  pe_ratio?: number | null;
  peg_ratio?: number | null;
}

export interface GlassdoorSummary {
  rating: number | null;
  snippet: string;
}

export interface PersonalizationData {
  narrative_summary?: string;
  focus_dimensions?: { label: string; relevance: number; rationale?: string }[];
  suggested_kpis?: { name: string; value: string; hint?: string }[];
  chart_series?: { priority_scores?: { name: string; score: number }[] };
  insights_from_chat?: { title: string; description: string; impact: string }[];
}

export interface IndustryData {
  companies: Company[];
  dimensions: Dimension[];
  sentimentTrends: SentimentTrend[];
  insights: Record<Audience, Insight[]>;
  praiseComplaintThemes?: PraiseComplaintTheme[];
  shareOfVoice?: ShareOfVoiceItem[];
  churnFlows?: ChurnFlow[];
  dimensionDeltas?: DimensionDelta[];
  personalization?: PersonalizationData;
  /** Google News headlines for the focal company — investors audience */
  newsHeadlines?: NewsHeadline[];
  /** Live stock quotes keyed by company name — investors audience */
  financeData?: Record<string, FinanceQuote>;
  /** Glassdoor employee ratings keyed by company name — companies + customers audience */
  glassdoorData?: Record<string, GlassdoorSummary>;
  /** AI-generated executive brief paragraph — present after Run Analysis */
  executiveBrief?: string;
  /** Customer-facing recommendations — present after Run Analysis */
  customerRecommendations?: { company: string; label: string; reason: string }[];
  /** Competitor gap analysis for companies audience — present after Run Analysis */
  competitorGap?: { theme: string; competitor_mentions: string[]; focal_status: string; impact: string; suggestion: string }[];
  _meta?: {
    industry: string;
    totalReviews: number;
    totalInsights: number;
    dataSource: string;
    reviewCountsFromDataset: boolean;
    isMock: boolean;
  };
}

export const industryData: Record<Industry, IndustryData> = {
  "food-delivery": {
    companies: [
      {
        id: "ubereats",
        name: "Uber Eats",
        price: 7.5,
        perceivedValue: 7.8,
        overallSentiment: 0.42,
        reviewCount: 125000,
        color: "#06C167",
      },
      {
        id: "doordash",
        name: "DoorDash",
        price: 7.2,
        perceivedValue: 7.5,
        overallSentiment: 0.38,
        reviewCount: 148000,
        color: "#FF3008",
      },
      {
        id: "grubhub",
        name: "Grubhub",
        price: 6.8,
        perceivedValue: 6.2,
        overallSentiment: 0.15,
        reviewCount: 89000,
        color: "#F63440",
      },
      {
        id: "deliveroo",
        name: "Deliveroo",
        price: 7.0,
        perceivedValue: 7.3,
        overallSentiment: 0.45,
        reviewCount: 72000,
        color: "#00CCBC",
      },
      {
        id: "justeat",
        name: "Just Eat",
        price: 6.5,
        perceivedValue: 6.5,
        overallSentiment: 0.22,
        reviewCount: 95000,
        color: "#FF8000",
      },
    ],
    dimensions: [
      {
        name: "Delivery Speed",
        importance: 95,
        scores: {
          ubereats: 82,
          doordash: 85,
          grubhub: 68,
          deliveroo: 88,
          justeat: 70,
        },
      },
      {
        name: "Food Quality",
        importance: 92,
        scores: {
          ubereats: 78,
          doordash: 76,
          grubhub: 72,
          deliveroo: 82,
          justeat: 74,
        },
      },
      {
        name: "App Experience",
        importance: 88,
        scores: {
          ubereats: 86,
          doordash: 84,
          grubhub: 65,
          deliveroo: 80,
          justeat: 68,
        },
      },
      {
        name: "Restaurant Selection",
        importance: 85,
        scores: {
          ubereats: 88,
          doordash: 90,
          grubhub: 78,
          deliveroo: 75,
          justeat: 82,
        },
      },
      {
        name: "Customer Support",
        importance: 82,
        scores: {
          ubereats: 72,
          doordash: 68,
          grubhub: 58,
          deliveroo: 75,
          justeat: 62,
        },
      },
      {
        name: "Pricing & Fees",
        importance: 90,
        scores: {
          ubereats: 58,
          doordash: 60,
          grubhub: 65,
          deliveroo: 62,
          justeat: 72,
        },
      },
    ],
    sentimentTrends: [
      { month: "Sep '25", ubereats: 0.38, doordash: 0.35, grubhub: 0.18, deliveroo: 0.42, justeat: 0.20 },
      { month: "Oct '25", ubereats: 0.40, doordash: 0.36, grubhub: 0.16, deliveroo: 0.44, justeat: 0.21 },
      { month: "Nov '25", ubereats: 0.39, doordash: 0.37, grubhub: 0.14, deliveroo: 0.43, justeat: 0.19 },
      { month: "Dec '25", ubereats: 0.41, doordash: 0.38, grubhub: 0.15, deliveroo: 0.45, justeat: 0.22 },
      { month: "Jan '26", ubereats: 0.43, doordash: 0.39, grubhub: 0.16, deliveroo: 0.46, justeat: 0.23 },
      { month: "Feb '26", ubereats: 0.42, doordash: 0.38, grubhub: 0.15, deliveroo: 0.45, justeat: 0.22 },
    ],
    insights: {
      investors: [
        {
          type: "opportunity",
          title: "DoorDash Market Leadership",
          description: "DoorDash maintains highest review volume (148K) and strong restaurant selection scores (90/100), indicating defensible market position despite pricing pressure.",
          impact: "high",
          metrics: ["148K reviews", "90/100 restaurant selection", "7.5/10 perceived value"],
        },
        {
          type: "risk",
          title: "Customer Support Vulnerability",
          description: "All players score below 75/100 on customer support, with Grubhub at critical 58/100. This represents sector-wide margin pressure risk as support costs increase.",
          impact: "high",
          metrics: ["Industry avg: 67/100", "Grubhub: 58/100", "Best performer: 75/100"],
        },
        {
          type: "trend",
          title: "Deliveroo Sentiment Momentum",
          description: "Deliveroo shows consistent sentiment growth (+7% QoQ) despite mid-tier pricing, suggesting product differentiation and customer loyalty.",
          impact: "medium",
          metrics: ["+7% sentiment QoQ", "45% positive sentiment", "7.3/10 value perception"],
        },
      ],
      companies: [
        {
          type: "opportunity",
          title: "Customer Support Gap",
          description: "Industry-wide weakness in customer support (avg 67/100). Companies that invest here can differentiate meaningfully. Top complaint themes: refund delays, driver communication.",
          impact: "high",
          metrics: ["All competitors <75/100", "32% of negative reviews cite support", "Est. 15% retention impact"],
        },
        {
          type: "risk",
          title: "Pricing Power Compression",
          description: "Pricing & Fees dimension shows lowest satisfaction (avg 63/100). Fee transparency and value perception are eroding, limiting ability to raise prices.",
          impact: "high",
          metrics: ["63/100 pricing satisfaction", "Just Eat leads at 72/100", "Price sensitivity up 12% YoY"],
        },
        {
          type: "trend",
          title: "Speed Expectations Rising",
          description: "Delivery speed importance climbed to 95/100. Customers now expect <30min delivery. Deliveroo leads (88/100) through micro-fulfillment centers.",
          impact: "medium",
          metrics: ["95/100 importance", "Deliveroo: 88/100", "<30min now baseline"],
        },
      ],
      customers: [
        {
          type: "opportunity",
          title: "Best for Speed: Deliveroo",
          description: "Deliveroo consistently delivers fastest with 88/100 score and highest positive sentiment (45%). Ideal for time-sensitive orders.",
          impact: "high",
          metrics: ["88/100 speed score", "45% positive sentiment", "Avg 23min delivery"],
        },
        {
          type: "risk",
          title: "Hidden Fee Alert",
          description: "Customer sentiment data reveals dissatisfaction with fee structures across all platforms. Just Eat rated most transparent (72/100) vs Uber Eats (58/100).",
          impact: "high",
          metrics: ["Just Eat: 72/100 fee transparency", "Uber Eats: 58/100", "Avg markup: 25-35%"],
        },
        {
          type: "trend",
          title: "Restaurant Variety Winner: DoorDash",
          description: "DoorDash offers widest selection (90/100) with 340K+ restaurant partnerships. Best for exploring new cuisines.",
          impact: "medium",
          metrics: ["90/100 selection score", "340K+ restaurants", "28% more options vs avg"],
        },
      ],
    },
  },
  "ride-sharing": {
    companies: [
      {
        id: "uber",
        name: "Uber",
        price: 8.2,
        perceivedValue: 8.0,
        overallSentiment: 0.35,
        reviewCount: 285000,
        color: "#000000",
      },
      {
        id: "lyft",
        name: "Lyft",
        price: 7.8,
        perceivedValue: 7.5,
        overallSentiment: 0.38,
        reviewCount: 178000,
        color: "#FF00BF",
      },
      {
        id: "bolt",
        name: "Bolt",
        price: 6.5,
        perceivedValue: 7.2,
        overallSentiment: 0.48,
        reviewCount: 95000,
        color: "#34D186",
      },
      {
        id: "freenow",
        name: "FreeNow",
        price: 7.5,
        perceivedValue: 7.0,
        overallSentiment: 0.32,
        reviewCount: 68000,
        color: "#FFC933",
      },
      {
        id: "didi",
        name: "DiDi",
        price: 6.8,
        perceivedValue: 6.8,
        overallSentiment: 0.28,
        reviewCount: 142000,
        color: "#FF7426",
      },
    ],
    dimensions: [
      {
        name: "Wait Time",
        importance: 94,
        scores: {
          uber: 85,
          lyft: 82,
          bolt: 88,
          freenow: 75,
          didi: 78,
        },
      },
      {
        name: "Driver Quality",
        importance: 91,
        scores: {
          uber: 78,
          lyft: 82,
          bolt: 85,
          freenow: 76,
          didi: 72,
        },
      },
      {
        name: "Safety Features",
        importance: 96,
        scores: {
          uber: 88,
          lyft: 86,
          bolt: 82,
          freenow: 80,
          didi: 75,
        },
      },
      {
        name: "Pricing Transparency",
        importance: 89,
        scores: {
          uber: 65,
          lyft: 68,
          bolt: 82,
          freenow: 72,
          didi: 70,
        },
      },
      {
        name: "App Reliability",
        importance: 87,
        scores: {
          uber: 82,
          lyft: 80,
          bolt: 78,
          freenow: 74,
          didi: 76,
        },
      },
      {
        name: "Payment Options",
        importance: 78,
        scores: {
          uber: 90,
          lyft: 85,
          bolt: 80,
          freenow: 82,
          didi: 88,
        },
      },
    ],
    sentimentTrends: [
      { month: "Sep '25", uber: 0.32, lyft: 0.36, bolt: 0.45, freenow: 0.30, didi: 0.26 },
      { month: "Oct '25", uber: 0.33, lyft: 0.37, bolt: 0.46, freenow: 0.31, didi: 0.27 },
      { month: "Nov '25", uber: 0.34, lyft: 0.38, bolt: 0.47, freenow: 0.31, didi: 0.27 },
      { month: "Dec '25", uber: 0.35, lyft: 0.37, bolt: 0.48, freenow: 0.32, didi: 0.28 },
      { month: "Jan '26", uber: 0.36, lyft: 0.39, bolt: 0.49, freenow: 0.33, didi: 0.29 },
      { month: "Feb '26", uber: 0.35, lyft: 0.38, bolt: 0.48, freenow: 0.32, didi: 0.28 },
    ],
    insights: {
      investors: [
        {
          type: "opportunity",
          title: "Bolt Value Proposition",
          description: "Bolt achieves highest sentiment (48%) at 20% lower price point than Uber, suggesting strong unit economics and defensible market position in price-sensitive segments.",
          impact: "high",
          metrics: ["48% positive sentiment", "20% price advantage", "6.5/10 pricing vs 8.2/10 Uber"],
        },
        {
          type: "risk",
          title: "Pricing Transparency Crisis",
          description: "Uber and Lyft score below 70/100 on pricing transparency (importance: 89/100). Regulatory risk as surge pricing scrutiny increases across markets.",
          impact: "high",
          metrics: ["Uber: 65/100", "Lyft: 68/100", "89/100 customer importance"],
        },
        {
          type: "trend",
          title: "Safety as Competitive Moat",
          description: "Safety features now top priority (96/100 importance). Uber's investment lead (88/100) creates switching costs and brand equity worth monitoring.",
          impact: "medium",
          metrics: ["96/100 importance", "Uber leads: 88/100", "13-point gap to #5"],
        },
      ],
      companies: [
        {
          type: "opportunity",
          title: "Pricing Transparency Whitespace",
          description: "Bolt leads transparency (82/100) while Uber/Lyft lag (65-68/100). Upfront, no-surge pricing could capture frustrated premium customers.",
          impact: "high",
          metrics: ["Bolt: 82/100", "Uber/Lyft: 65-68/100", "Top complaint: surge pricing"],
        },
        {
          type: "risk",
          title: "Driver Quality Compression",
          description: "Your driver quality scores may be below Bolt (85/100) and Lyft (82/100). Driver churn and rating inflation mask real experience gaps.",
          impact: "medium",
          metrics: ["Bolt: 85/100", "Lyft: 82/100", "DiDi: 72/100"],
        },
        {
          type: "trend",
          title: "Wait Time Expectations Tightening",
          description: "Wait time importance at 94/100. Bolt leads (88/100) with proactive driver positioning. <5min wait now expected in urban areas.",
          impact: "medium",
          metrics: ["94/100 importance", "Bolt: 88/100", "<5min urban baseline"],
        },
      ],
      customers: [
        {
          type: "opportunity",
          title: "Best for Safety: Uber",
          description: "Uber offers most comprehensive safety features (88/100) including real-time GPS sharing, emergency assistance, and in-ride audio recording.",
          impact: "high",
          metrics: ["88/100 safety score", "Real-time GPS sharing", "24/7 support line"],
        },
        {
          type: "risk",
          title: "Surge Pricing Alert",
          description: "Uber and Lyft have lowest pricing transparency scores. Bolt offers upfront pricing with no surge fees - can save 30-40% during peak times.",
          impact: "high",
          metrics: ["Bolt: 82/100 transparency", "Uber: 65/100", "Save 30-40% on surge"],
        },
        {
          type: "trend",
          title: "Fastest Pickups: Bolt",
          description: "Bolt consistently provides fastest pickup times (88/100) with average 3.5min urban wait vs 5.2min industry average.",
          impact: "medium",
          metrics: ["88/100 wait time score", "3.5min avg urban wait", "30% faster than avg"],
        },
      ],
    },
  },
  "saas": {
    companies: [
      {
        id: "slack",
        name: "Slack",
        price: 7.5,
        perceivedValue: 8.2,
        overallSentiment: 0.62,
        reviewCount: 48000,
        color: "#4A154B",
      },
      {
        id: "teams",
        name: "Microsoft Teams",
        price: 6.5,
        perceivedValue: 7.5,
        overallSentiment: 0.45,
        reviewCount: 72000,
        color: "#5059C9",
      },
      {
        id: "zoom",
        name: "Zoom",
        price: 7.0,
        perceivedValue: 7.8,
        overallSentiment: 0.58,
        reviewCount: 56000,
        color: "#2D8CFF",
      },
      {
        id: "discord",
        name: "Discord",
        price: 4.5,
        perceivedValue: 7.0,
        overallSentiment: 0.68,
        reviewCount: 125000,
        color: "#5865F2",
      },
      {
        id: "webex",
        name: "Webex",
        price: 6.8,
        perceivedValue: 6.5,
        overallSentiment: 0.32,
        reviewCount: 32000,
        color: "#00BCEB",
      },
    ],
    dimensions: [
      {
        name: "Ease of Use",
        importance: 93,
        scores: {
          slack: 92,
          teams: 75,
          zoom: 90,
          discord: 88,
          webex: 68,
        },
      },
      {
        name: "Video Quality",
        importance: 88,
        scores: {
          slack: 78,
          teams: 82,
          zoom: 95,
          discord: 85,
          webex: 80,
        },
      },
      {
        name: "Integration Ecosystem",
        importance: 90,
        scores: {
          slack: 95,
          teams: 88,
          zoom: 75,
          discord: 72,
          webex: 78,
        },
      },
      {
        name: "Enterprise Security",
        importance: 92,
        scores: {
          slack: 88,
          teams: 92,
          zoom: 85,
          discord: 65,
          webex: 90,
        },
      },
      {
        name: "Mobile Experience",
        importance: 82,
        scores: {
          slack: 88,
          teams: 72,
          zoom: 85,
          discord: 90,
          webex: 70,
        },
      },
      {
        name: "Pricing Value",
        importance: 85,
        scores: {
          slack: 72,
          teams: 85,
          zoom: 78,
          discord: 95,
          webex: 70,
        },
      },
    ],
    sentimentTrends: [
      { month: "Sep '25", slack: 0.60, teams: 0.43, zoom: 0.56, discord: 0.66, webex: 0.30 },
      { month: "Oct '25", slack: 0.61, teams: 0.44, zoom: 0.57, discord: 0.67, webex: 0.31 },
      { month: "Nov '25", slack: 0.62, teams: 0.44, zoom: 0.57, discord: 0.67, webex: 0.31 },
      { month: "Dec '25", slack: 0.61, teams: 0.45, zoom: 0.58, discord: 0.68, webex: 0.32 },
      { month: "Jan '26", slack: 0.63, teams: 0.46, zoom: 0.59, discord: 0.69, webex: 0.33 },
      { month: "Feb '26", slack: 0.62, teams: 0.45, zoom: 0.58, discord: 0.68, webex: 0.32 },
    ],
    insights: {
      investors: [
        {
          type: "opportunity",
          title: "Discord Community Monetization",
          description: "Discord achieves highest sentiment (68%) at lowest price (4.5/10) with 125K reviews. Strong viral growth and monetization potential through premium features.",
          impact: "high",
          metrics: ["68% positive sentiment", "125K reviews", "Lowest churn rate segment"],
        },
        {
          type: "risk",
          title: "Microsoft Teams Enterprise Lock-in",
          description: "Teams scores 92/100 on enterprise security with bundled M365 pricing advantage (85/100 pricing value). Threatens standalone collaboration tool margins.",
          impact: "high",
          metrics: ["92/100 security", "85/100 pricing value", "Bundled with M365"],
        },
        {
          type: "trend",
          title: "Integration Ecosystem as Moat",
          description: "Slack's integration lead (95/100) creates switching costs. 90/100 importance signals network effects and platform defensibility.",
          impact: "high",
          metrics: ["Slack: 95/100 integrations", "90/100 importance", "2,500+ app directory"],
        },
      ],
      companies: [
        {
          type: "opportunity",
          title: "Mobile Experience Gap",
          description: "Discord leads mobile (90/100) while Teams lags (72/100). Hybrid work demands mobile-first design - clear differentiation opportunity.",
          impact: "high",
          metrics: ["Discord: 90/100", "Teams: 72/100", "82/100 importance"],
        },
        {
          type: "risk",
          title: "Ease of Use Vulnerability",
          description: "If you score below Slack (92/100) on usability, churn risk is significant. Complexity drives users to Discord despite lower enterprise features.",
          impact: "high",
          metrics: ["Slack: 92/100", "93/100 importance", "#1 switching reason"],
        },
        {
          type: "trend",
          title: "Video Quality Table Stakes",
          description: "Zoom dominates video (95/100) with 88/100 importance. Video reliability is now baseline expectation, not differentiator.",
          impact: "medium",
          metrics: ["Zoom: 95/100", "88/100 importance", "All competitors investing"],
        },
      ],
      customers: [
        {
          type: "opportunity",
          title: "Best for Teams: Slack",
          description: "Slack offers superior ease of use (92/100), best integration ecosystem (95/100), and highest overall satisfaction (62% positive sentiment).",
          impact: "high",
          metrics: ["92/100 usability", "95/100 integrations", "62% positive sentiment"],
        },
        {
          type: "risk",
          title: "Enterprise Security Gaps",
          description: "Discord scores only 65/100 on enterprise security vs Microsoft Teams (92/100). Not suitable for sensitive business communications.",
          impact: "high",
          metrics: ["Discord: 65/100 security", "Teams: 92/100", "Webex: 90/100"],
        },
        {
          type: "trend",
          title: "Best Value: Discord",
          description: "Discord provides 95/100 pricing value with robust free tier and $10/month premium. Best for community-focused teams on budget.",
          impact: "medium",
          metrics: ["95/100 pricing value", "$0-10/month", "68% positive sentiment"],
        },
      ],
    },
  },
};

export const audienceDescriptions: Record<Audience, string> = {
  investors: "Focus on defensible moats, competitive margins, and market dynamics",
  companies: "Identify customer pain points, competitive gaps, and strategic opportunities",
  customers: "Compare platforms based on real user experiences and value for money",
};

export const industryNames: Record<Industry, string> = {
  "food-delivery": "Food Delivery",
  "ride-sharing": "Ride-Sharing",
  "saas": "SaaS Collaboration",
  "crm": "CRM Software",
};
