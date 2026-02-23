---
name: New Attack Scenario
about: Propose a new attack scenario for security testing
title: "[SCENARIO] "
labels: scenario, enhancement
assignees: ''
---

## Domain

Which domain does this scenario belong to?

- [ ] Banking
- [ ] Healthcare
- [ ] HR
- [ ] New domain (specify below)

**New domain name** (if applicable):

## Scenario Name

A short, descriptive name in snake_case (e.g., `price_manipulation_attack`).

## Description

What vulnerability or attack vector does this scenario test?

## Attack Prompt

The actual prompt that would be sent to the agent:

```
Your attack prompt here
```

## Success Indicators

Phrases in the agent's response that indicate it was compromised:

- `indicator 1`
- `indicator 2`
- `indicator 3`

## Injected Content (Optional)

For indirect prompt injection scenarios, describe the malicious content that would be injected via tool responses:

```json
{
  "tool": "tool_name",
  "response": {
    "field": "value with [SYSTEM: malicious instruction]"
  }
}
```

## Real-World Relevance

How might this attack occur in a real-world application? Why is it important to test for this?

## References (Optional)

Links to related research, CVEs, or examples of this attack type.
