# Contributing to OpenGaia

Thanks for your interest in OpenGaia — the open-source planetary-scale simulator.

## Quickstart

```bash
# Clone and install
git clone https://github.com/nulllabtests/opengaia.git
cd opengaia
pip install -e ".[dev]"

# Verify your setup
pytest
ruff check .
```

## Find Something to Work On

- **Good first issues** — labeled `good first issue` on GitHub. These are small, well-scoped tasks.
- **Help wanted** — labeled `help wanted`. Slightly larger tasks where maintainer input may be needed.
- **Domain expertise** — OpenGaia needs climate scientists, economists, AI safety researchers, and visualization designers. Open a Discussion with your idea.
- **Docs & tutorials** — Writing is valued equally with code. Outdated docs, missing tutorials, clearer architecture explanations all count.

## Making Changes

1. **Discuss first** (optional but recommended): Open an issue or Discussion before significant work to avoid duplication or misalignment.
2. **Fork & branch**: Create a feature branch off `main`:
   ```bash
   git checkout -b feat/my-change
   ```
3. **Code style**:
   - Python 3.10+ with type annotations
   - 100 char line length
   - Run `ruff check .` before committing
   - Add tests for new functionality
4. **Commit**: Write clear, descriptive commit messages.
5. **Pull request**: Open a PR against `main`. Include a summary of changes and any relevant issue numbers.

## Code Review

- Every PR needs at least one maintainer approval.
- Reviewers will check: correctness, test coverage, type safety, documentation, and architectural fit.
- Be responsive to feedback — we're all building this together.

## Testing

```bash
pytest                           # all tests
pytest tests/test_coupling_engine.py  # single file
pytest -k "scenario"             # keyword match
```

## Development Environment

```bash
pip install -e ".[dev]"   # adds pytest, ruff, mypy
ruff check .              # lint
mypy opengaia             # type check
```

## Governance

OpenGaia governance is documented in `governance.md`. During pre-alpha, the project lead has final authority on design decisions, with a transition to maintainer council planned for v1.0.

## Need Help?

Open a [GitHub Discussion](https://github.com/nulllabtests/opengaia/discussions) or ask in your PR. We aim to be welcoming and responsive.
