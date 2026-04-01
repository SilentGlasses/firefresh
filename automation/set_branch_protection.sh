#!/usr/bin/env bash
set -euo pipefail

# Configure required status checks for branch protection via GitHub CLI.
# Usage:
#   automation/set_branch_protection.sh <owner/repo> [branch]
# Example:
#   automation/set_branch_protection.sh SilentGlasses/firefresh main

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required. Install it and retry."
  exit 1
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <owner/repo> [branch]"
  exit 1
fi

REPO="$1"
BRANCH="${2:-main}"

# Verify authentication before making API calls.
gh auth status >/dev/null

# Force PRs, strict up-to-date checks, and the required CI checks.
cat <<EOF | gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/${REPO}/branches/${BRANCH}/protection" \
  --input -
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "PR Quality Checks / quality-security",
      "Dependency Review / dependency-review",
      "CodeQL / Analyze (Python)",
      "Workflow Lint / actionlint"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "block_creations": false
}
EOF

echo "Branch protection configured for ${REPO}:${BRANCH}."
