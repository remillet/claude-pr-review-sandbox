# Sandbox: delete after testing

Throwaway test of the Claude PR review workflow (draft of `ets-berkeley-edu/claude-pr-review`), running on
Amazon Bedrock in a personal AWS sandbox account. The role ARN is a repo-level Actions secret.
`.github/workflows/pr-review.yml` calls this repo's own reusable workflow at a pinned SHA, the same way other repos will.
