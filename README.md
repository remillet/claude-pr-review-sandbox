# Claude PR review on Amazon Bedrock

Automatic Claude review of pull requests in ets-berkeley-edu repos. Inference runs in our AWS account through
Amazon Bedrock; GitHub authenticates to AWS with OIDC, so no AWS keys or Anthropic API keys are stored anywhere.

| Piece | File | Where it lives |
| - | - | - |
| IAM role (Bedrock invoke only, OIDC-trusted) | [aws/claude-pr-review-role.yaml](aws/claude-pr-review-role.yaml) | CloudFormation stack, once per AWS account |
| Reusable review workflow (prompt, model, tools) | [.github/workflows/claude-review.yml](.github/workflows/claude-review.yml) | This repo, `ets-berkeley-edu/claude-pr-review` |
| Caller workflow, ~20 lines | [examples/caller-claude-review.yml](examples/caller-claude-review.yml) | Each repo that opts in |

The AWS piece is standalone CloudFormation rather than Terraform because repos differ: Serena and BMU use
Terraform, others use none, and one shared role shouldn't belong to any single repo's state.

## One-time setup

1. **Bedrock model access.** In the Bedrock console (Model catalog), submit the Anthropic use-case form if the
   account hasn't, and make sure Claude Opus 5.5 is available for the `us.` cross-region profile.

2. **Deploy the role.** This needs IAM rights to create roles. In the UC Berkeley account the RTL-Developer
   permission set doesn't have them (it can't even list OIDC providers), so Ops deploys it, as with Serena's
   pipeline roles. Set `CreateOidcProvider=true` only if the account has no GitHub OIDC provider yet (Serena's
   open question DP2 to Ops).

   Each repo is identified by its OIDC subject, exactly as GitHub issues it. Repos with immutable subjects (as
   cspace-media-server has) include numeric IDs:

   ```bash
   gh api repos/ets-berkeley-edu/cspace-media-server/actions/oidc/customization/sub
   ```

   Use its `sub_claim_prefix` (if there is none, the subject is `repo:OWNER/REPO`):

   ```bash
   aws cloudformation deploy --stack-name claude-pr-review --template-file aws/claude-pr-review-role.yaml --capabilities CAPABILITY_NAMED_IAM --parameter-overrides GitHubSubjects=repo:ets-berkeley-edu@283538/cspace-media-server@1410958489
   ```

   ```bash
   aws cloudformation describe-stacks --stack-name claude-pr-review --query "Stacks[0].Outputs[?OutputKey=='RoleArn'].OutputValue" --output text
   ```

3. **Org secret.** In the ets-berkeley-edu org settings, add the Actions secret `CLAUDE_REVIEW_AWS_ROLE_ARN` with that
   ARN, with repository access set to **selected repositories**. (Not strictly secret, but it keeps the account
   number out of public files.)

4. **Publish this repo** as `ets-berkeley-edu/claude-pr-review` (public, so other org repos can call the workflow).
   Tag a release and pin callers to its commit SHA.

## Adding a repo

1. Add the repo's OIDC subject (`gh api repos/OWNER/REPO/actions/oidc/customization/sub`) to `GitHubSubjects`
   and redeploy the stack (the role trusts only listed repos).
2. Add the repo to the org secret's selected repositories.
3. Copy `examples/caller-claude-review.yml` to the repo's `.github/workflows/claude-review.yml`, fill in the SHA.
4. Optional: a `CLAUDE.md` at the repo root gives Claude project-specific review rules.

Once most repos are in, `repo:ets-berkeley-edu@283538/*` covers every repo with immutable subjects; add
`repo:ets-berkeley-edu/*` only if some repos still use the default subject.

Public and private repos both work. This repo must stay public so private repos can call its workflow (a
private callee would need its Actions access setting opened to the org). Private repos use Actions minutes from
the org's plan; public repos don't.

## Behavior

- Runs on PR open, push, reopen and ready-for-review. Skips drafts, bot PRs and **fork PRs** (GitHub gives fork
  runs no OIDC token; this is deliberate: `pull_request_target` is never used).
- Posts inline comments on findings, or one "no issues" comment.
- Claude can read the checkout and the PR, and comment. It can't push, run arbitrary commands, or reach other AWS
  services.
- Bounded by `--max-turns 30`, a 20-minute job timeout, and cancel-on-new-push.

## Data handling

PR diffs and the files Claude reads are sent to Bedrock in our AWS account. AWS doesn't use Bedrock inputs to
train models or share them with Anthropic. Before enabling repos that handle student data (BOAC, Damien,
Diablo), confirm this fits the data classification for that system; the review prompt also flags personal data
showing up in diffs.

## Cost controls

- Consider an AWS Budget alarm filtered to Bedrock.
- Switch to Sonnet 5.5 per repo via the caller's `model` input (redeploy the role with `BedrockModel=claude-sonnet-5-5`
  or a second stack, since the role allows one model).
- Drop `synchronize` from the caller's trigger types to review only on open/ready instead of every push.
