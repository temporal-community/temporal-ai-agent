# Experiment 001: Setup and run locally out of the box demo

**Date**:

## Objective
To understand what's involved in setting up and running the Temporal AI Agent locally out of the box demo.

## Setup

### Environment
- Local development environment
  - I'm using asdf (already installed)to manage python versions
  - Temporal is already installed using brew, `brew install temporal`

- Temporal server running
  - Start server using make commands: `make start-temporal-server `

### Configuration
Copy `.env.example` to `.env` and configure
- Set `LLM_KEY=YOUR_API_KEY`
- Set `LLM_MODEL=YOUR_MODEL_NAME`, e.g `anthropic/claude-3-5-sonnet-20240620`
- Set `STRIPE_API_KEY=` to generate mock data, use your Stripe API key if you have one


## Implementation Steps

Start local Temporal server
`make start-temporal-server`

Start api, workers, workflow and UI
`make run-dev`

Temporal workflow monitor
- URL is displayed in the output when server is started

Application UI


## Observations

### What Worked Well
- Point 1
- Point 2

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
