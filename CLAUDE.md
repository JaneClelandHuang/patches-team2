# Team rules for this repo

This is a team project. Every change goes through a pull request.

- Never commit or push to `main`. Work on a feature branch: one task, one branch, one PR.
- Never merge a PR. Merging is the team's decision; open the PR and stop.
- Every change comes with tests. Run `pytest` and make sure it passes before opening a PR.
- Before asking for review, merge the latest `main` into the branch and resolve any conflicts.
  Explain each conflict to the user and let them choose the resolution.
- Keep changes small and explain them. The student must be able to explain every line.

## Project basics
- Run the app: `python -m patches [puzzle.json]`
- Run tests: `pytest`
- Code layout: see README.md

## Pull request descriptions
When opening a PR, fill in `.github/pull_request_template.md` instead of writing a free-form
description. Put the issue number after `Closes #`. Leave "What Claude did / what I decided" for
the user to complete, or draft it and ask the user to check it.
