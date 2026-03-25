# Contributing to hotbunk

Thanks for your interest. Here is everything you need to get started.

## Setup

```bash
git clone https://github.com/drewbeyersdorf/hotbunk.git
cd hotbunk
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

All tests must pass before you open a PR.

## Pull requests

- PRs go to `main`.
- Describe **what** changed and **why**.
- Keep PRs focused. One logical change per PR.
- If your PR fixes an issue, reference it (e.g., `Fixes #12`).

## Code style

- Python 3.12+.
- Use type hints on all function signatures.
- Prefer dataclasses over plain dicts for structured data.
- No em dashes in code, comments, docs, or commit messages. Use hyphens or double hyphens instead.
- Keep functions short. If a function needs a scroll bar, split it.

## Reporting bugs and requesting features

Use the issue templates in `.github/ISSUE_TEMPLATE/`. Include enough detail for someone else to reproduce the problem or understand the request.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
