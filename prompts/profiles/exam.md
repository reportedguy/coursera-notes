---
id: profile-exam@v1
---
# Add-on: exam

Applies on top of any profile when `flags.exam` is true: the course prepares the learner for a named certification or standardized exam (for example a cloud certification or a PMI exam). It adds sections; it never removes the profile's.

## Important means
In addition to the profile's list:
- Exam domains, objectives and weights the course states. Use weights only when the source gives them.
- Distinctions the course says the exam probes (two similar services, two similar terms).
- Facts the course marks as "on the exam" or "know this".
- Question styles and traps the course describes.

## Module page
Add this section just before `## Recap`:

`## Exam focus`: 
- `### What the exam tests here`: the exam objective or domain this module covers, as the course names it.
- `### Know cold`: 5–12 bullets of facts the course says to memorize, each one line.
- `### Easy to confuse`: a table `| A | B | How to tell them apart |` of the look-alikes the course separates.
- `### Traps`: the wrong answers and misreadings the course warns about, one line each.

## Course map
Add after the profile's sections:
- `## Exam blueprint`: a table `| Domain | Weight | Modules |`. Leave Weight empty for any domain whose weight the source does not state.
- `## Final review`: one `- [ ]` checklist of every "Know cold" fact across modules, grouped by domain.

## Mind map
- Under each topic that an exam domain names, add a first bullet `Exam: <domain>`.

## Questions
- Keep every scenario-style question, even when it looks easy; the exam uses that style.
- Each "why" line also names why the most tempting wrong option is wrong, when the feedback says so.
