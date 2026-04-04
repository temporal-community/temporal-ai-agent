# Experiment 002: Run basic demo using Groq models

**Date**: 6/26/25

## Objective
Get the out of the box demo using Groq for LLM models


## Setup

### Environment
- Same as in basic workflow no changes

### Configuration
- Uncomment the Groq LLM configuration in .env

## Implementation Steps
- Start temporal server: `make start-temporal-server`
- Start the apis, workers, etc.: `make run-dev`
- Run the demo

## Observations
- Groq is fast!!!
- Quickly burn through the free tokens as Groq is rate limiting my free plan requests
- The demo handles the rate limit without crashing
- Workflow will timeout gracefully after 30 minutes, and app will stay alive
- Demo doesn't have any messaging about service provider hitting rate limiting

### What Worked Well

### Challenges Encountered
- Challenge 1
  - Solution/Workaround:
- Challenge 2
  - Solution/Workaround:

## Key Learnings

1. Learning 1
   - Details...
2. Learning 2
   - Details...

## Questions to Explore
- [ ] Question 1
- [ ] Question 2

## Next Steps
- [ ] What to try next
- [ ] Areas to improve

## Resources Used
- Link 1
- Link 2

## Code Snippets and Examples

### Example 1: Description
```python
# Add example code here
```

### Example 2: Description
```python
# Add example code here
```

## Notes for Future Reference
- Important note 1
- Important note 2

---
Last Updated:
