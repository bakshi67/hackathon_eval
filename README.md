# Hackathon Evaluation App (`hackathon_eval`)

Full evaluation management system for 562 hackathon teams across 3 levels on Frappe Framework (v15).
See root [README.md](../README.md) for full architecture and user runbook.

### Quick Start
```bash
# Run unit tests
bench --site hackathon.localhost run-tests --app hackathon_eval

# Run demo seed
bench --site hackathon.localhost execute hackathon_eval.seed.run
```
