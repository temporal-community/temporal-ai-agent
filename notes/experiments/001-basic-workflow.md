# Experiment 001: Setup and run locally out of the box demo

**Date**:

## Objective
To understand what's involved in setting up and running the Temporal AI Agent locally out of the box demo.

## State
Can start everything up back create a new chat.
Looking through Temporal serves messages, I see warnings about "Activity failure size exceeds limit for mutable state"

The LLM provider isn't configured in the .env file. For that matter I don't event have a .env failure

**Try**
 - Create a .env file by copying `.env.example` and configure, and see what happens
 - Configured LLM using NF key
**Result**
- NF key is crap, it is always out of tokens

**Try**
 - Configure with LLama to not burn tokens while testing
 - NOt working, needs some code changes to get Ollama to working

**Try**
- Configure using my Anthropic key
**Result**
  - Starts up okay, and I can interact with chat bot
  - I get 10 "welcome" messages though



## Setup

### Environment
- [ ] Local development environment
  - I'm using asdf (already installed)to manage python versions
  - Temporal is already installed using brew, `brew install temporal`
- [ ] Temporal server running
  - Start server using make commands: `make start-temporal-server `

### Configuration
```yaml
# Add any relevant configuration here
```

## Implementation Steps

1. **Initial Setup**
   - [ ] Task
   - Notes:

2. **Workflow Definition**
   - [ ] Task
   - Code changes:
   ```python
   # Add code snippets here
   ```

3. **Agent Integration**
   - [ ] Task
   - Notes:

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
