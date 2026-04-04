# Build: Suncatcher Manufacturing Cost Calculator

## What I Need
A web-based tool I'll actually use in my workshop to understand true cost-per-unit
and set profitable pricing for my suncatcher products. This is a real business tool,
not a demo.

## My Manufacturing Process (Complete)
Each suncatcher goes through these steps in order:

### Step 1: 3D Print Frame/Base
- Machine: [printer model]
- Filament: [type, brand]
- Cost per roll: $[X] for [weight] from Amazon
- Estimated grams per unit: [X]g (including supports/waste)
- Print time per unit: [X] minutes
- Failure/scrap rate: ~[X]% (failed prints, adhesion issues, etc.)

### Step 2: Laser Engrave/Cut Acrylic
- Machine: xTool P2 CO2 and/or xTool F2 Ultra MOPA fiber
- Acrylic stock: [size] sheets, $[X] per sheet from [source]
- Units per sheet: [X] (accounting for kerf and spacing)
- Machine time per unit: [X] minutes
- Waste rate: ~[X]% (cracked pieces, alignment errors)
- Consumables: CO2 tube replacement every ~[X] hours ($[X])

### Step 3: UV Print Color Layer
- Machine: EufyMake E1
- Ink cost: $[X] per cartridge set
- Estimated prints per cartridge set: [X]
- Machine time per unit: [X] minutes
- Waste rate: ~[X]% (misprints, alignment issues)

### Step 4: Assembly
- Additional materials: [glue, hardware, etc. with costs]
- Assembly time per unit: [X] minutes

### Step 5: Finishing/Packaging
- Packaging materials: $[X] per unit
- Packaging time: [X] minutes

## Machine Inventory (for depreciation)
| Machine | Purchase Price | Expected Lifespan | Annual Hours Used |
|---------|---------------|-------------------|-------------------|
| 3D Printer [model] | $[X] | [X] years | ~[X] hrs |
| xTool P2 CO2 | $[X] | [X] years | ~[X] hrs |
| xTool F2 Ultra MOPA | $[X] | [X] years | ~[X] hrs |
| EufyMake E1 | $[X] | [X] years | ~[X] hrs |

## Other Overhead
- Electricity estimate: ~$[X]/kWh
- My labor rate: $[X]/hour (what I want to pay myself)
- Workspace cost: $[X]/month (or $0 if home workshop, no allocation)
- Amazon shipping: [Prime member? Per-order shipping costs?]

## Verification Data (Critical)
Here's a real project I've already made and roughly costed:
- Product: [specific suncatcher design]
- Actual materials used: [specifics]
- Actual time spent: [X] minutes total
- What I think it costs me: ~$[X] per unit
- What I've been charging: $[X]
The calculator MUST get within 15% of my known cost. If it doesn't, the model is wrong.

## Functional Requirements
- [ ] Accurate cost-per-unit breakdown: materials, machine time, labor, depreciation, overhead
- [ ] Input a new product's specs and see instant cost breakdown
- [ ] Set target margin percentage, see recommended retail price
- [ ] Save projects for future reference (persistent storage)
- [ ] Dashboard showing all products and their margins
- [ ] Editable material prices (costs change, Amazon prices fluctuate)
- [ ] Compare different production approaches (P2 vs F2 for same cut, for example)

## Operating Instructions
You are the **planner and judge dispatcher** for this build. You do NOT write implementation code directly. Run autonomously using sub-agents:

1. **Plan the build order.** Cost model engine first, then UI, then persistence.
   Produce a brief PLAN.md. Do not dispatch implementation until the plan exists.

2. **Dispatch a worker agent to build the cost model engine.**
   Give it: the full manufacturing process data, the cost categories, and the
   verification data (my real project with known cost). Include permission scope:
   allowed paths, allowed operations, forbidden operations.
   The worker builds the engine and returns the module.

3. **Dispatch a separate judge agent to verify the cost model.**
   Give it: the verification project data and the cost model module (no
   implementation reasoning). The judge runs my known project through the model
   and checks: does it land within 15%? Are all cost categories accounted for?
   Does the math make sense? If it fails, take the judge's findings and
   dispatch a new worker to fix it.

4. **Once the cost model is verified, dispatch a worker to build the UI.**
   Practical, clean, workshop-friendly. Not a design showcase.
   I need to use this with dirty hands and limited patience.
   Build as a React artifact with persistent storage.

5. **Dispatch a judge to verify the full tool.**
   - Cost model: does the math check out against my known project?
   - UI: does every input actually affect the calculation correctly?
   - Persistence: do saved projects survive across sessions?
   - Edge cases: what happens with zero quantities, missing inputs, extreme values?

6. **Maintain state throughout.** Use `templates/PROGRESS.md` format for your state file.
   Record side-effects and checkpoints for each completed task.

7. **Only come to me when:**
   - The cost model doesn't match my verification data and you need more production details
   - There's a UX decision that depends on how I actually work (e.g., do I batch or make one-offs?)
   - The tool is ready for me to test with real numbers

8. **When you're done**, present the working tool and show me the cost breakdown
   for my verification project so I can sniff-check the math immediately.
