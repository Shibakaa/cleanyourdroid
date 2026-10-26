## What changed

<!-- One or two sentences. Link the issue if there is one. -->

## Type

- [ ] New or updated device profile (`devices/`)
- [ ] Database change (`safety/`)
- [ ] Tool or test change (`tools/`, `tests/`)
- [ ] Documentation only

## Safety checklist

- [ ] `python -m unittest discover -s tests -v` passes
- [ ] `python tools/plan.py --validate` passes
- [ ] No package was added to `known_bloatware.json` without testing it on a real device
- [ ] Every new action has a recorded reverse command (`log-action` / `tune.py`)
- [ ] Nothing requires root

## Evidence

<!-- For device profiles: build id, before/after numbers, and what you reverted, if anything. -->
