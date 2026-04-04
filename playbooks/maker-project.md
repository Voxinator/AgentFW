# Scenario: Personal Manufacturing Cost Calculator (Web Tool)

> Extracted from the AgentFW Playbook — Scenario 3.

**Context:** You want to build a web-based pricing tool for your personal maker business. You're producing suncatchers using a multi-step manufacturing process: 3D printing (filament), laser engraving (xTool P2 CO2 or F2 Ultra MOPA), UV printing (EufyMake E1), and acrylic stock. Materials come from Amazon. You need to understand true cost per unit to price correctly.

## The Harness Setup

This is a build project where you have irreplaceable domain knowledge — your actual manufacturing process, real costs, machine quirks, and waste rates. Claude can plan and dispatch workers to build and judges to verify, but it needs your production reality as input. The autonomous mode front-loads all that domain knowledge so Claude can run the full build without interruption.

---

## Option A: Autonomous Mode (Recommended)

One launch prompt with your complete production data. Claude builds the full tool — cost model engine, UI, persistence — and comes back with a working product for you to verify against real numbers.

See `templates/launch-prompts/autonomous-maker.md` for the standalone launch prompt template.

**What makes this different from guided mode:** You're giving Claude your complete domain knowledge upfront — the entire manufacturing process, real costs, real waste rates, machine inventory. That's the harness. With all of that loaded, Claude can plan, dispatch workers to build, dispatch judges to verify, and iterate — all without you in the loop until the final sniff-check. Your re-entry point is testing it against reality.

---

## Option B: Guided Mode (Step-by-Step)

Use this if you're still figuring out your own production process and want to think through the cost model conversationally before building anything. Also useful if you want to iterate on the UI design interactively.

### Step 1: Process Mapping (Planner Mode)

Before any code, map the manufacturing process. This is the domain knowledge that Claude doesn't have.

```
I'm building a web-based cost calculator for my suncatcher production.
Before we build anything, help me map out the cost model.

My manufacturing process:
1. 3D print a frame/base (filament: [type], [cost per roll], [estimated grams per unit])
2. Laser engrave design onto acrylic (xTool P2 or F2 Ultra MOPA)
   - Acrylic sheets: [size, cost per sheet, units per sheet]
   - Machine time: [estimated minutes per unit]
3. UV print color layer (EufyMake E1)
   - Ink cost: [cost per cartridge set, estimated prints per set]
   - Machine time: [estimated minutes per unit]
4. Assembly: [any additional materials, time estimate]

Cost categories I need to track:
- Raw materials (filament, acrylic, ink)
- Machine consumables (laser tube life, print head life)
- Machine time (electricity, depreciation)
- My time (labor rate I want to pay myself)
- Amazon shipping / per-unit material cost
- Waste/scrap rate
- Packaging and shipping to customer (if applicable)

Help me build the cost model BEFORE we build the UI.
What am I missing? What should I track that I'm not thinking about?
```

### Step 2: Decompose the Build

```
Now let's plan the tool itself. Decompose this into buildable pieces:

Piece 1: Cost Model Engine
- Input: material costs, machine parameters, labor rate
- Output: cost per unit with full breakdown
- Verify by: I can manually check the math against a known project

Piece 2: Material Database
- Track my actual Amazon purchase prices over time
- Calculate per-unit material costs (e.g., $25 roll / X grams per unit)
- Handle multi-pack pricing, shipping costs

Piece 3: Machine Cost Calculator
- Depreciation over expected lifespan
- Consumable replacement schedule
- Power consumption estimates
- Per-minute operating cost for each machine

Piece 4: Pricing Interface
- Input a new product's specs
- See full cost breakdown
- Set target margin
- Get recommended retail price
- Compare different production approaches

Piece 5: Project History
- Save past projects with actual costs
- Track estimated vs actual over time
- See which products are most/least profitable

Build these as independent modules. Which should we start with?
```

### Step 3: Build Iteratively (Worker Mode)

Start with the cost model engine — it's the foundation and it's machine-checkable (the math is either right or it isn't). Claude operates as the worker:

```
Let's build Piece 1: the Cost Model Engine.

Requirements:
- Takes raw inputs: material costs, quantities, machine time, labor time
- Calculates: material cost, machine cost, labor cost, overhead, total cost per unit
- Outputs a full breakdown I can review line by line

Build this as a standalone module first. I want to verify the math
against a real project before we add any UI.

Here's a real example to test against:
- [Your actual suncatcher project with known costs]
- I know this costs me approximately $X to make
- The calculator should get within 10% of that
```

After Claude builds each piece, **you verify it against your real production data.** You are the domain expert AND the judge — only you know your actual costs, machine quirks, and waste rates. Claude builds; you verify against reality.

If you want automated verification for the math (does the calculator match the test data?), dispatch a **separate sub-agent** with the verification data and the built module. Don't ask the session that built the cost model to also assess whether its own math is correct.

### Step 4: Layer on the UI

Only after the cost model is verified:

```
The cost model is solid. Now let's build the pricing interface.

I want a clean, practical tool — not a flashy demo.
This is a tool I'll actually use in my workshop.
I need to use this with dirty hands and limited patience.

Key interactions:
- Quick-add a new project: select machines used, enter material quantities
- See instant cost breakdown as I enter specs
- Set my target margin (e.g., 40%) and see the price
- Save the project for future reference
- Dashboard showing all my products and their margins

Build this as a React artifact I can use.
Use persistent storage so my projects survive across sessions.
```

---

## Key Principles for the Cost Calculator

- **You are the domain expert AND the judge.** Only you know your actual production costs, machine quirks, and waste rates. Claude builds the tool; you verify it against reality.
- **Real data is your Tier 1 verification.** Test every calculation against actual projects you've already costed out by hand (or by gut feel). If the numbers don't match your experience, the model is wrong.
- **Start with the math, not the UI.** The cost model engine is the core value. If the math is right but the UI is ugly, you still have a useful tool. If the UI is beautiful but the math is wrong, you have nothing.
- **Account for the things that are easy to forget:** waste/scrap rate, failed prints, machine warm-up time, material that's consumed but doesn't end up in the product (laser kerf, support material, purge lines).
- **Your Amazon purchase history is a data source.** Track actual prices paid over time, not listed prices. Prices fluctuate, shipping costs vary, and multi-pack vs single pricing matters.
- **Depreciation is real.** Your xTool P2, F2 Ultra, EufyMake E1, and 3D printer all have finite lifespans. The cost per unit should include a fraction of the machine cost amortized over its expected total output.
