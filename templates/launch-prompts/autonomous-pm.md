# Feature Investigation: [Feature Name]

## Current Intake Status
New Request → heading toward ROM and Investigation

## Business Request
- Requested by: [who]
- What they want: [their words, not yours yet]
- Why: [business driver]
- Value stream: [Your Value Stream]
- Key stakeholders: [list names and roles]

## Known Context
- Integration points I'm aware of: [list known systems and services]
- Related past work: [any previous features or investigations that touch this area]
- Political/organizational context: [anything Claude needs to know about stakeholder dynamics,
  budget sensitivity, competing priorities]

## Domain Knowledge
- [How this area of the product actually works today — the stuff that isn't in Jira]
- [Known technical debt or constraints in the affected area]
- [Things other PMs or engineers have mentioned about this space]

## Constraints
- Feature scope target: 12-16 weeks max
- Investigation accuracy target: +/-75%
- Current strategic theme: [your org's current theme, e.g., stability and predictability]
- Must align to OKRs: [list the specific KRs this could connect to]
- Budget status: [known / unknown / needs funding request]

## Operating Instructions
You are the **planner and judge dispatcher** for this investigation. Run autonomously using sub-agents:

1. **Decompose the investigation into parallel research tracks** (this is planning — do it yourself):
   - Technical landscape (what exists, what it touches, architecture implications)
   - Business requirements (users, use cases, scope boundaries)
   - Effort & complexity (modules affected, cross-team dependencies, estimated size)
   - Risk & dependencies (blockers, competing work, backward compatibility)

2. **Dispatch worker agents for each research track.** Each worker receives:
   - The track's specific questions to answer
   - The relevant domain knowledge and constraints from this prompt
   - Permission scope: read-only investigation, no system modifications
   - Instructions to flag assumptions vs. facts
   Workers produce findings. You evaluate and synthesize across tracks.

3. **Dispatch a worker agent to produce the deliverables** from the synthesized findings:
   - Investigation document (using our standard template): problem statement, scope,
     effort vs value, conceptual design, projected solution, resources, timeline, risks
   - Stakeholder questions list: questions I need to take to real humans that you can't answer
   - Risk register: what could block or derail this
   - Recommended next steps: what needs to happen to move from Investigation to Investigation Complete

4. **Dispatch a separate judge agent to review the deliverables.** The judge receives:
   - The original business request and constraints (from this prompt)
   - The produced deliverables
   - This checklist to evaluate against:
     - Does the scope fit 12-16 weeks?
     - Are estimates within +/-75%?
     - Did it identify all cross-team dependencies?
     - Does this align with current strategic theme?
     - Is there a quantitative value proposition? (OKR: 50% of features need one)
     - Has it accounted for vendor/contractor resource rotation risk?
     - Is benefit realization measurement defined? (needed for 1/3/6-month assessments)
     - Can leadership sniff-check this in 5 minutes? (Decisions and recommendations up front, detail underneath)
   If the judge finds gaps, dispatch a new worker to address them.

5. **Maintain state throughout.** Use `templates/PROGRESS.md` format for your state file.
   Record side-effects and checkpoints for each completed task.

6. **Only come to me when:**
   - You need stakeholder input or business context I haven't provided
   - There's an architectural decision that requires engineering input I'd need to go get
   - The investigation is complete and ready for my review

7. **When you're done**, present: the investigation document, the questions I need to
   go ask humans, and your confidence level on each section (high/medium/low).
