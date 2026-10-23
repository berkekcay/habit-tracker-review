# Week 6 writeup: guardrails, agent PRs, and human vs AI review

Implementing agent: Claude Code (Opus 5.5), one one-shot prompt per task.
AI reviewer: **CodeRabbit** (GitHub app, review profile "chill"). I tried Copilot review first;
it refused because the account's free review quota was used up.

## Pull requests

| Task | PR | Commits |
| --- | --- | --- |
| 2. Validation | [#1](https://github.com/berkekcay/habit-tracker-review/pull/1) | [agent one-shot](https://github.com/berkekcay/habit-tracker-review/commit/e058d5f), [my review fixes](https://github.com/berkekcay/habit-tracker-review/commit/3e6271e) |
| 1. Streak | [#2](https://github.com/berkekcay/habit-tracker-review/pull/2) | [agent one-shot](https://github.com/berkekcay/habit-tracker-review/commit/33318ef), [my review fixes](https://github.com/berkekcay/habit-tracker-review/commit/48f7ff6), [CodeRabbit fix](https://github.com/berkekcay/habit-tracker-review/commit/b8c51d0) |

Each PR description has the problem, approach, testing and tradeoffs. I also opened
[#3](https://github.com/berkekcay/habit-tracker-review/pull/3) and
[#4](https://github.com/berkekcay/habit-tracker-review/pull/4) with only the agent's commit
for each task, so CodeRabbit could review the same code I reviewed by hand. Both were closed
without merging.

## Guardrails

```bash
pip install -r requirements-dev.txt   # black 26.10.1, ruff 0.17.2, pytest
black --check .                       # formatting
ruff check .                          # lint: pyflakes, pycodestyle, import order, bugbear, pyupgrade
pytest                                # behavior
```

`.github/workflows/ci.yml` runs the same three commands on every push and PR, and any failure
fails the build. I formatted the starter with black in its own commit first, so the feature
diffs only show real changes.

- **pytest fails the build.** The `guardrail-demo` branch adds a test that expects a 500 from
  `GET /habits`. Locally `pytest` exits with 1, and
  [the CI run](https://github.com/berkekcay/habit-tracker-review/actions/runs/39927812562) fails.
- **What black and ruff catch.** On a six-line file with sloppy code, black reports
  "1 file would be reformatted" and ruff finds unsorted imports (I001), two unused imports
  (F401), a mutable default argument (B006), `== None` (E711) and two statements on one line
  (E701). None of those would show up as a failing test.

## My review vs CodeRabbit

**Validation (#1).** The agent's version worked and had 16 tests. Reading the diff line by line,
I found:

1. no upper limit on the habit name, so a 10 MB name would be stored;
2. every message started with Pydantic's "Value error, " prefix, which isn't the "clear
   message" the task asks for;
3. the missing-name test only checked the status code;
4. the same day can be checked in twice, and future days are accepted (left for the streak
   task, since that isn't malformed input).

CodeRabbit on the agent-only version (#3) posted no actionable comments. On the final PR it
also had nothing actionable, flagged docstring coverage at 0%, and its security summary
mentioned the missing duplicate suppression, which was my point 4. Its docstring warning is
noise for a 100-line app where black, ruff and the tests already describe the code.

**Streak (#2).** The agent returned a streak of 0 whenever there was no check-in yet today,
so a 30-day streak would look broken every morning. I read "up to and including today" as a
window and changed it: a run ending yesterday stays current, and a missed yesterday resets it.
I also made the 404 test check the body, and noted in the PR that "today" is the server's
timezone.

CodeRabbit on the agent-only version (#4) found nothing; its summary said "No actionable
streak defect is established", so the morning-zero behavior went through. On the final PR it caught one thing I missed: the README still said the
streak ends today, after I had added the yesterday rule. I applied its suggestion.

**Where each was better.** My review found the issues that need a judgement about what the
user expects: a reasonable length limit, readable messages, what a "current" streak means.
CodeRabbit didn't question the agent's reading of the task at all. It was better at
consistency between files: the stale README line was a real bug in the docs, and I didn't
look at the README again after changing the code. It also read the PR descriptions and
echoed them (on #4 it noted that the PR "is intended to be closed"), so a confident
description can steer it.

## What I learned

Guardrails and AI review cover different things. black, ruff and pytest are cheap, they never
disagree with themselves, and they stop formatting, lint and regression problems before
anyone reads the diff. The AI reviewer was good at small consistency checks but approved code
that I had found three real problems in, so I would treat a clean AI review as "nothing
obvious", not as approval. I'd keep it as a second reader after my own review, mainly for
docs and cross-file drift, and keep the product decisions with a human.
