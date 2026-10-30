---
id: mindmap@v2
---
# Course mind map

Input: the course's module pages and the course's `profile.json` (path in your task; `<data_root>/pages/<course>/profile.json` if none is named). Output: a markdown outline that renders as an interactive mind map. Someone should be able to grasp the course's whole shape at a glance, then expand any branch to see its key points.

Format, nothing else:
```
# <Course title>
## Module 1: <short module title>
### <Topic>
- <key point>
  - <detail>
### <Topic>
## Module 2: …
```

Profile: the `## Mind map` part of `prompts/profiles/<type>.md` (and of `prompts/profiles/exam.md` when `flags.exam` is true) says what the key points under each topic are. It fills the slot below. If the slot still reads `{{PROFILE}}` literally, read those files yourself. If base and profile conflict, the base wins.

{{PROFILE}}

Rules:
- Level 1 is the course, and there is exactly one. Level 2 is the modules. Level 3 is each module's main topics, as they appear in its page (3–7 per module).
- Every node is 7 words or fewer, a noun phrase or an imperative. No sentences, no punctuation at the end.
- No examples, no stories, no links, no images. No names of people, unless the profile says the person or work is the subject.
- Cover everything structural in the module pages, and nothing that isn't there.
- Step counts and step order match the module pages exactly.

Write the outline to the output path in your task. Reply with one line: the node count.
