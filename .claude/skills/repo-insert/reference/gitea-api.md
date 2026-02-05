# Gitea API Reference for Door43

## Token Setup

1. Log in to [git.door43.org](https://git.door43.org)
2. Go to **Settings** > **Applications**: `https://git.door43.org/user/settings/applications`
3. Under **Manage Access Tokens**, enter a name (e.g., "claude-code") and click **Generate Token**
4. Copy the token and add it to your `.env` file:
   ```
   DOOR43_TOKEN=your-token-here
   ```

The token is only needed for creating PRs via the REST API. All git operations (clone, push, pull) use SSH keys.

## API Endpoints

Base URL: `https://git.door43.org/api/v1`

### Create Pull Request

```
POST /repos/{owner}/{repo}/pulls
```

Headers:
```
Content-Type: application/json
Authorization: token {DOOR43_TOKEN}
```

Body:
```json
{
  "title": "PR title",
  "head": "source-branch",
  "base": "target-branch",
  "body": "Description (optional)"
}
```

Response includes `html_url` (the PR link) and `number`.

### List Pull Requests

```
GET /repos/{owner}/{repo}/pulls?state=open
```

### Get Repository Info

```
GET /repos/{owner}/{repo}
```

### List Branches

```
GET /repos/{owner}/{repo}/branches
```

## Organization

All unfoldingWord repos are under the `unfoldingWord` organization:
- ULT: `unfoldingWord/en_ult`
- UST: `unfoldingWord/en_ust`
- TN: `unfoldingWord/en_tn`

## SSH URLs

For git operations (clone, push, pull):
```
git@git.door43.org:unfoldingWord/en_ult.git
git@git.door43.org:unfoldingWord/en_ust.git
git@git.door43.org:unfoldingWord/en_tn.git
```
