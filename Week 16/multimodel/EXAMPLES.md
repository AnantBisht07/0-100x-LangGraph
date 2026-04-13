# Usage Examples - Conversational Planner Agent

## Example 1: Trip Planning (Text)

```
You: text: Plan a 5-day trip to Paris for a couple

[ROUTER] Input type detected: text
[TEXT PROCESSOR] Processing text input...
[PLANNER] Starting planning process...

Planner: Let me create a romantic 5-day Paris itinerary for two:

DAY 1 - Arrival & Orientation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Morning:
- Arrive at CDG Airport
- Check into hotel in Le Marais district
- Light lunch at local café

Afternoon:
- Walk along Seine River
- Visit Notre-Dame Cathedral (exterior)
- Explore Île de la Cité

Evening:
- Dinner at traditional bistro
- Evening stroll at Pont Neuf

DAY 2 - Iconic Paris
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Morning:
- Eiffel Tower (pre-book tickets)
- Trocadéro Gardens photo stop

Afternoon:
- Lunch at Champ de Mars
- Arc de Triomphe visit
- Champs-Élysées shopping

Evening:
- Seine River cruise (sunset)
- Dinner in Montmartre

DAY 3 - Art & Culture
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Morning:
- Louvre Museum (arrive early)
- Mona Lisa, Venus de Milo

Afternoon:
- Tuileries Garden walk
- Musée d'Orsay (Impressionists)

Evening:
- Latin Quarter dinner
- Jazz club or wine bar

DAY 4 - Hidden Gems
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Morning:
- Montmartre neighborhood
- Sacré-Cœur Basilica
- Artists' square

Afternoon:
- Le Marais vintage shopping
- Jewish quarter exploration

Evening:
- Dinner at rooftop restaurant
- Optional: Moulin Rouge show

DAY 5 - Versailles & Departure
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Morning:
- Day trip to Versailles Palace
- Gardens exploration

Afternoon:
- Return to Paris
- Last-minute shopping
- Airport transfer

Budget Estimate: €2,500-3,500 for two
Includes: Accommodation, meals, attractions, transport

Would you like me to adjust anything?

[Turn 1 | Summary: 0 chars | Type: text]
```

---

## Example 2: Follow-up with Voice Input (Mock)

```
You: voice: What about budget hotels?

[ROUTER] Input type detected: voice
[VOICE PROCESSOR] Processing voice input...
[VOICE PROCESSOR] Mock: Transcribing 'What about budget hotels?'
[PLANNER] Starting planning process...

Planner: For budget-friendly accommodation in Paris, here are excellent options:

BUDGET HOTELS IN PARIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Le Marais Area (Central):
• Hôtel de Nice - €80-120/night
  - Charming, 17th century building
  - Near metro, restaurants
  - Breakfast included

• BVJ Paris - €60-90/night
  - Youth hostel style
  - Clean, modern rooms
  - Group-friendly

Latin Quarter:
• Hôtel Esmeralda - €70-110/night
  - Notre-Dame views
  - Vintage charm
  - Popular with couples

• Select Hotel - €85-130/night
  - Boutique feel
  - Eco-friendly
  - Good breakfast

Montmartre:
• Hôtel Bonséjour - €65-95/night
  - Near Sacré-Cœur
  - Local neighborhood feel
  - Affordable

Money-Saving Tips:
✓ Book directly (skip booking fees)
✓ Stay Sunday-Thursday (cheaper)
✓ Look for breakfast included
✓ Consider Airbnb for longer stays

Updated Budget: €1,800-2,500 for two
(With budget hotels vs. mid-range)

Shall I update the itinerary with these hotels?

[Turn 2 | Summary: 0 chars | Type: voice]
```

---

## Example 3: Image Input for Context (Mock)

```
You: image: Photo of cherry blossoms in bloom

[ROUTER] Input type detected: image
[IMAGE PROCESSOR] Processing image input...
[IMAGE PROCESSOR] Mock: Analyzing 'Photo of cherry blossoms in bloom'
[PLANNER] Starting planning process...

Planner: Based on the cherry blossoms, I see you're interested in spring travel! Let me adjust the Paris plan for spring season:

SPRING IN PARIS (March-May)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best Time: Late March - Early May
Peak Bloom: Early-Mid April

UPDATED ITINERARY - SPRING FOCUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DAY 2 - Gardens & Blooms
• Jardin du Luxembourg (cherry trees!)
• Parc des Buttes-Chaumont (magnolias)
• Tuileries Garden (tulips)

DAY 3 - Seine Banks
• Promenade Plantée (elevated park)
• Coulée Verte (green corridor)
• Picnic by river

DAY 4 - Versailles Gardens
• Spring fountain show (Apr-Oct)
• Marie-Antoinette's gardens
• Grand Trianon blooms

SPRING-SPECIFIC TIPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Pack light jacket (15-20°C)
✓ Bring sunglasses (longer days)
✓ Book outdoor cafés
✓ Visit flower markets

Cherry Blossom Spots:
• Parc de Sceaux (30 min from Paris)
• Square Jean XXIII
• Jardin des Plantes

Spring Events:
• Paris Marathon (early April)
• Foire du Trône (spring fair)
• Outdoor concerts begin

This season offers perfect weather for your romantic trip!

[Turn 3 | Summary: 0 chars | Type: image]
```

---

## Example 4: Project Planning

```
You: text: I need to launch a SaaS product in 6 months with $50k budget

[ROUTER] Input type detected: text
[TEXT PROCESSOR] Processing text input...
[PLANNER] Starting planning process...

Planner: Let me break down your SaaS launch into a structured 6-month plan:

SAAS PRODUCT LAUNCH PLAN (6 MONTHS, $50K)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 1: DISCOVERY & PLANNING (Month 1) - $5K
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week 1-2: Market Research
□ Competitor analysis
□ Target audience definition
□ Problem-solution fit validation
□ Survey 50-100 potential users

Week 3-4: Product Planning
□ Feature prioritization (MVP scope)
□ Technical architecture design
□ Budget allocation finalization
□ Roadmap creation

Deliverables:
✓ Product Requirements Document
✓ Technical spec
✓ 6-month roadmap
✓ Go-to-market strategy outline

PHASE 2: MVP DEVELOPMENT (Months 2-3) - $20K
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Month 2: Core Features
□ User authentication system
□ Core feature #1 development
□ Database setup
□ Basic UI/UX implementation

Month 3: Essential Features
□ Core feature #2 & #3
□ Payment integration (Stripe)
□ Email notifications
□ Admin dashboard

Team Structure:
• 1 Full-stack developer ($8K/month)
• 1 Part-time designer ($2K/month)
• Cloud hosting ($500/month)

PHASE 3: TESTING & REFINEMENT (Month 4) - $8K
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week 1-2: Beta Testing
□ Recruit 20 beta users
□ Collect feedback
□ Track key metrics
□ Bug fixes

Week 3-4: Refinement
□ UI/UX improvements
□ Performance optimization
□ Security audit
□ Documentation

PHASE 4: MARKETING PREP (Month 4-5) - $10K
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Content Creation:
□ Landing page ($2K)
□ Product demo video ($1.5K)
□ Blog content (10 articles)
□ Email drip campaign

Pre-Launch Marketing:
□ Social media setup
□ Product Hunt preparation
□ Press kit creation
□ Early access list building

PHASE 5: LAUNCH (Month 6) - $7K
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week 1-2: Soft Launch
□ Product Hunt launch
□ Email list activation
□ Social media campaign
□ Influencer outreach ($2K)

Week 3-4: Full Launch
□ Paid ads ($3K)
□ PR campaign
□ Customer support setup
□ Metrics tracking

BUDGET BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Development:          $20,000 (40%)
Marketing:            $10,000 (20%)
Testing & QA:         $8,000  (16%)
Design:               $5,000  (10%)
Infrastructure:       $3,000  (6%)
Contingency:          $4,000  (8%)
────────────────────────────────
Total:                $50,000

KEY MILESTONES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Month 1: Product plan complete
✓ Month 3: MVP functional
✓ Month 4: Beta testing complete
✓ Month 5: Marketing assets ready
✓ Month 6: Public launch

SUCCESS METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 100 beta users by Month 4
• 500 sign-ups by Month 6
• 50 paying customers by Month 6
• $5K MRR by Month 6

RISKS & MITIGATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk: Development delays
→ Build MVP-first, defer nice-to-haves

Risk: Budget overrun
→ 8% contingency buffer, track weekly

Risk: Low user adoption
→ Pre-validate with surveys, beta test

What aspect would you like me to detail further?

[Turn 1 | Summary: 0 chars | Type: text]
```

---

## Example 5: Memory Compression Demo

```
[Turns 1-4 shown above...]

You: text: What tech stack should I use?

[ROUTER] Input type detected: text
[TEXT PROCESSOR] Processing text input...
[PLANNER] Starting planning process...

Planner: For your SaaS product with a $50K budget and 6-month timeline, here's a recommended tech stack:

RECOMMENDED TECH STACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FRONTEND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Framework: React + Next.js
Why:
✓ Fast development
✓ SEO-friendly
✓ Large talent pool (affordable devs)
✓ Great documentation

UI Library: Tailwind CSS + shadcn/ui
Why:
✓ Rapid prototyping
✓ Beautiful defaults
✓ Free components

State Management: Zustand
Why:
✓ Simple API
✓ Less boilerplate than Redux
✓ Good performance

...

[Turn 5 | Summary: 0 chars | Type: text]

[MEMORY] Compression triggered at turn 5
[MEMORY] Compressing conversation history...
[MEMORY] Summary updated (312 chars)

You: text: How do I handle customer support?

[ROUTER] Input type detected: text
[TEXT PROCESSOR] Processing text input...
[PLANNER] Starting planning process...

Planner: Given your SaaS launch plan with $50K budget, here's a customer support strategy:

CUSTOMER SUPPORT STRATEGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 1: PRE-LAUNCH (Free)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Email support only
• Founder handles personally
• Response within 24 hours
• Build knowledge base

PHASE 2: EARLY DAYS ($100/month)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tools:
• Intercom or Crisp Chat
• Help Scout for ticketing
• Documentation in Notion

Team:
• Founder + 1 part-time support

...

[Turn 6 | Summary: 312 chars | Type: text]

Note: Turns 1-4 compressed into summary, only recent turns kept in full!
```

---

## Example 6: Multi-Input Conversation

```
You: text: Plan a home office renovation

Planner: Let me help you plan your home office renovation:

INITIAL QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Space size: What are the dimensions?
2. Budget: What's your renovation budget?
3. Work type: What do you do? (Developer, designer, etc.)
4. Must-haves: Standing desk, storage, etc.?

Please provide:
- Room dimensions or a photo
- Budget range
- Your profession/work needs

[Turn 1]

You: image: Current office with cluttered desk

[IMAGE PROCESSOR] Processing image input...
[IMAGE PROCESSOR] Mock: Analyzing 'Current office with cluttered desk'

Planner: Based on the current office image, I can see:

CURRENT STATE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Observations:
- Small desk, limited workspace
- Cable management needed
- Poor lighting
- Lack of storage
- No ergonomic setup

RENOVATION PRIORITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Larger desk with cable management
2. Better lighting (natural + task)
3. Storage solutions
4. Ergonomic chair
5. Wall organization

Would you like a budget estimate for these improvements?

[Turn 2]

You: voice: Budget is around 5000 dollars

[VOICE PROCESSOR] Processing voice input...
[VOICE PROCESSOR] Mock: Transcribing 'Budget is around 5000 dollars'

Planner: Perfect! With a $5,000 budget, here's a comprehensive renovation plan:

$5,000 HOME OFFICE RENOVATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FURNITURE ($2,500)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Standing desk (Uplift V2): $800
• Ergonomic chair (Herman Miller Aeron used): $600
• Storage cabinet: $400
• Shelving unit: $300
• Monitor arms (dual): $200
• Desk organizers: $200

TECHNOLOGY ($1,200)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 27" monitor upgrade: $400
• Webcam + mic: $300
• Desk lamp (BenQ): $200
• Cable management: $100
• Power strip/UPS: $200

LIGHTING ($800)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• LED ceiling light: $300
• Task lighting: $200
• Smart bulbs (Philips Hue): $300

AESTHETICS ($500)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Paint: $200
• Artwork/decor: $200
• Plants: $100

TIMELINE: 2-3 weeks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week 1: Furniture delivery, painting
Week 2: Setup, cable management
Week 3: Final touches, organization

Shall I create a shopping list with links?

[Turn 3]
```

---

## Example 7: Complex Planning with Clarifications

```
You: text: Build a mobile fitness app

Planner: Great idea! Before I create a detailed plan, I need to understand your goals:

CLARIFYING QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. TARGET AUDIENCE
   □ Beginners?
   □ Intermediate fitness enthusiasts?
   □ Athletes/professionals?
   □ Specific age group?

2. CORE FEATURES
   □ Workout tracking?
   □ Meal planning?
   □ Progress analytics?
   □ Social features?
   □ Video workouts?
   □ Personal trainer matching?

3. MONETIZATION
   □ Subscription model?
   □ Freemium?
   □ One-time purchase?
   □ Ad-supported?

4. CONSTRAINTS
   □ Budget?
   □ Timeline?
   □ Team size?
   □ Technical expertise?

5. COMPETITIVE ADVANTAGE
   □ What makes it different from:
     - MyFitnessPal
     - Strava
     - Nike Training Club
     - Peloton

Please answer these, and I'll create a comprehensive plan!

[Turn 1]

You: text: Beginners, workout tracking + meal plans, freemium model, 100k budget, 8 months, team of 4

Planner: Perfect! Here's your comprehensive fitness app plan:

BEGINNER FITNESS APP - 8 MONTH PLAN ($100K)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APP CONCEPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: FitStart (working title)
Tagline: "Your first step to fitness"

Target: Fitness beginners (ages 25-45)
Key Features:
✓ Simple workout tracking
✓ Beginner-friendly meal plans
✓ Progress visualization
✓ Community support

FREEMIUM MODEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Free Tier:
• Basic workouts (bodyweight)
• Simple meal suggestions
• Progress tracking
• Limited to 3 workouts/week

Premium ($9.99/month):
• Unlimited workouts
• Custom meal plans
• Video demonstrations
• Personal trainer chat
• Advanced analytics
• Ad-free experience

DEVELOPMENT ROADMAP (8 MONTHS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MONTH 1-2: PLANNING & DESIGN ($15K)
□ User research (interviews with 50 beginners)
□ Competitor analysis
□ Feature prioritization
□ Wireframing
□ UI/UX design
□ Branding

MONTH 3-5: MVP DEVELOPMENT ($45K)
Core Features:
□ User auth & onboarding
□ Workout library (50 exercises)
□ Workout tracking
□ Basic meal plans (20 recipes)
□ Progress dashboard
□ Subscription system

MONTH 6: TESTING ($10K)
□ Beta testing (100 users)
□ Bug fixes
□ Performance optimization
□ Analytics implementation

MONTH 7-8: LAUNCH & MARKETING ($30K)
□ App store optimization
□ Content marketing
□ Influencer partnerships
□ Paid ads
□ PR campaign

... [Full detailed plan continues]

[Turn 2]
```

---

## Summary of Examples

These examples demonstrate:

1. **Text Input** - Standard planning queries
2. **Voice Input** - Hands-free follow-ups (mock)
3. **Image Input** - Visual context for planning (mock)
4. **Memory Compression** - Auto-compress after turn 5
5. **Multi-Input** - Combining text, voice, image
6. **Clarification** - Asking questions before planning
7. **Complex Planning** - Detailed project breakdown

**Key Patterns:**
- All inputs normalize to text
- Planner provides structured output
- Memory compresses to prevent overflow
- Streaming shows progress
- Metadata tracks processing details
