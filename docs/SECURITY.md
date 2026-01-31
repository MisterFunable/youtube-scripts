# Security Best Practices

Guidelines for protecting sensitive data and API credentials in this repository.

## Critical: Files to Never Commit

The following files contain sensitive data and MUST NEVER be committed to version control:

### API Credentials
- `client_secret*.json` - OAuth 2.0 credentials from Google Cloud Console
- `token.pickle` - Cached authentication tokens
- `token.json` - Alternative token format
- Any `*.pickle` files (may contain auth data)

### Environment Variables
- `.env` - Contains API keys (OpenAI, YouTube)
- `.env.local`, `.env.production` - Environment-specific configs

### Generated Data
- `video_list.json` - May contain unpublished video metadata
- `videos_today.json` - Current video data
- `video_queue.json` - Videos pending processing
- `processed.json` - Processing history
- `custom_translations.json` - May contain proprietary content
- `video_settings.json` - Channel-specific settings

### Backup Files
- `backups/` directory - May contain historical sensitive data
- `*_backup_*.json` - Timestamped backups
- `*copy*.json` - Duplicate files

## Verification

### Check .gitignore

Ensure `.gitignore` is properly configured:

```bash
# View current gitignore
cat .gitignore

# Test what would be committed
git status --ignored

# Verify sensitive files are ignored
git check-ignore client_secret.json token.pickle .env
# Should output the filenames (meaning they're ignored)
```

### Before First Commit

```bash
# Scan for API keys in code
grep -r "AIzaSy" .
grep -r "sk-" .  # OpenAI keys
grep -r "client_secret" .

# Should only find references, not actual keys
```

### Check Staged Files

```bash
# Before committing, always review
git status
git diff --cached

# Unstage sensitive file accidentally added
git reset HEAD client_secret.json
```

## API Key Management

### YouTube Data API

**OAuth Credentials** (`client_secret.json`):
- Download from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Store in project root
- Never hardcode in scripts
- Rotate if compromised

**API Keys** (if using):
- Not recommended (OAuth is preferred)
- If used, store in `.env` file
- Never pass as URL parameters in logs

### OpenAI API

**API Keys**:
- Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- Store in `.env` file:
  ```bash
  OPENAI_API_KEY=sk-your-key-here
  ```
- Never log or print keys
- Rotate monthly or after suspected exposure

### Environment Variables

**Setup**:
```bash
# Create .env file (ignored by git)
cat > .env << EOF
OPENAI_API_KEY=sk-your-key-here
YOUTUBE_API_KEY=optional-key-here
EOF

# Verify it's ignored
git check-ignore .env
```

**Usage in scripts**:
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Never print keys
# print(api_key)  # BAD!
if api_key:
    print("API key loaded")  # GOOD
```

## Token Security

### Understanding Tokens

**`token.pickle`**:
- Contains OAuth access token and refresh token
- Grants full access to your YouTube account
- Expires but can be refreshed indefinitely
- Must be protected like a password

**What can someone do with your token?**
- Upload/delete videos
- Modify video metadata
- Access private video data
- Manage playlists
- All operations your account can perform

### Token Protection

```bash
# Set restrictive permissions
chmod 600 client_secret.json
chmod 600 token.pickle
chmod 600 .env

# Verify permissions
ls -la | grep -E "(client_secret|token|\.env)"
# Should show: -rw------- (owner read/write only)
```

### Token Rotation

**Revoke compromised tokens**:

1. Delete local token:
   ```bash
   rm token.pickle
   ```

2. Revoke app access:
   - Go to [Google Account Permissions](https://myaccount.google.com/permissions)
   - Find your app
   - Click "Remove Access"

3. Re-authenticate:
   ```bash
   python3 video-fetching/list_videos.py --test
   ```

## Hardcoded Secrets Detection

### Common Mistakes to Avoid

```python
# BAD - Hardcoded API key
api_key = "AIzaSyABCDEF123456789"

# GOOD - From environment
api_key = os.getenv('YOUTUBE_API_KEY')
```

```python
# BAD - Logging sensitive data
print(f"Using API key: {api_key}")

# GOOD - Log safely
print("API key loaded successfully")
```

```bash
# BAD - In bash script
curl -H "Authorization: Bearer sk-abc123" https://api.openai.com

# GOOD - From environment
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com
```

### Scan for Leaked Secrets

```bash
# Search for potential API keys
grep -r "AIzaSy" . --exclude-dir=.git
grep -r "sk-[a-zA-Z0-9]" . --exclude-dir=.git
grep -r "client_secret.*:" . --exclude-dir=.git

# Search for hardcoded tokens
grep -r "ya29\." . --exclude-dir=.git  # Google access tokens
grep -r "access_token" . --exclude-dir=.git
```

## Git History Cleanup

### If Secrets Were Committed

**Option 1: Remove from recent history** (if not pushed):
```bash
# Remove file from last commit
git reset HEAD~1
rm client_secret.json  # or move to safe location
git add .
git commit -m "Remove sensitive file"
```

**Option 2: Rewrite history** (if already pushed):
```bash
# Use git-filter-repo (recommended)
pip install git-filter-repo
git filter-repo --path client_secret.json --invert-paths

# Force push (coordinate with team!)
git push origin --force --all
```

**Option 3: Use BFG Repo-Cleaner**:
```bash
# Download BFG
# https://rtyley.github.io/bfg-repo-cleaner/

# Remove file from history
bfg --delete-files client_secret.json

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

**CRITICAL**: After removing secrets from history:
1. Rotate ALL exposed credentials immediately
2. Revoke compromised tokens
3. Notify anyone with repo access
4. Consider making repo private

## Data Privacy

### Video Metadata

**What's sensitive?**
- Unpublished video titles/descriptions
- View counts (may reveal business metrics)
- Publication dates (may reveal content strategy)
- Private/unlisted video data

**Protection**:
- Don't commit `video_list.json` or similar exports
- Use `.github-ready-review/` for sensitive data inspection
- Sanitize data before sharing examples

### Translation Content

**What's sensitive?**
- `custom_translations.json` - May contain proprietary vocabulary
- `video_settings.json` - Reveals channel strategy

**Protection**:
- Provide example templates only (`.example.json`)
- Keep actual files in `.gitignore`

## Deployment Security

### Production Environments

**Use environment variables**:
```bash
# Set in production server
export OPENAI_API_KEY="sk-production-key"
export YOUTUBE_API_KEY="production-yt-key"

# Or use secrets manager
# AWS: AWS Secrets Manager
# Google Cloud: Secret Manager
# Azure: Key Vault
```

**Docker security**:
```dockerfile
# Don't bake secrets into images
# BAD
ENV OPENAI_API_KEY=sk-abc123

# GOOD - Pass at runtime
# docker run -e OPENAI_API_KEY=$OPENAI_API_KEY ...
```

### Cloud Deployment

**Use managed secrets**:
- AWS Systems Manager Parameter Store
- Google Cloud Secret Manager
- Azure Key Vault
- HashiCorp Vault

**Example (Google Cloud)**:
```bash
# Store secret
gcloud secrets create openai-key --data-file=- <<< "sk-abc123"

# Access in code
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = "projects/PROJECT_ID/secrets/openai-key/versions/latest"
response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode("UTF-8")
```

## Monitoring

### Detect Suspicious Activity

**YouTube API**:
- Monitor quota usage in [Google Cloud Console](https://console.cloud.google.com/)
- Unusual spikes may indicate token compromise
- Check [recent account activity](https://myactivity.google.com/myactivity)

**OpenAI API**:
- Monitor usage in [OpenAI Dashboard](https://platform.openai.com/usage)
- Set spending limits
- Enable email alerts for unusual activity

### Audit Logs

```bash
# Review git commits for accidental secrets
git log --all --pretty=format:"%H %s" | while read hash msg; do
  if git show $hash | grep -q "AIzaSy\|sk-"; then
    echo "⚠️  Potential secret in: $hash - $msg"
  fi
done
```

## Incident Response

### If Credentials Are Compromised

**Immediate steps**:

1. **Revoke access**:
   - Delete OAuth tokens (local and cloud)
   - Revoke app permissions
   - Rotate API keys

2. **Assess impact**:
   - Check YouTube channel for unauthorized changes
   - Review API usage logs
   - Check OpenAI billing for unexpected costs

3. **Rotate credentials**:
   - Generate new OAuth client ID
   - Create new API keys
   - Update all deployment environments

4. **Clean repository**:
   - Remove secrets from git history
   - Force push cleaned history
   - Notify collaborators

5. **Document incident**:
   - What was exposed?
   - How long was it exposed?
   - What actions were taken?
   - How to prevent recurrence?

### Prevention

- [ ] Use `.gitignore` properly
- [ ] Store secrets in environment variables
- [ ] Never hardcode credentials
- [ ] Scan commits before pushing
- [ ] Use pre-commit hooks
- [ ] Regular credential rotation
- [ ] Principle of least privilege (minimal scopes)
- [ ] Monitor API usage regularly

## Pre-Commit Hooks

### Install Secrets Scanner

```bash
# Install gitleaks
# https://github.com/gitleaks/gitleaks

# macOS
brew install gitleaks

# Linux
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz
tar -xzf gitleaks_8.18.1_linux_x64.tar.gz

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
gitleaks protect --staged --verbose
if [ $? -ne 0 ]; then
  echo "❌ Secrets detected! Commit aborted."
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

### Test Hook

```bash
# Try to commit a secret
echo "OPENAI_API_KEY=sk-abc123" > test_secret.txt
git add test_secret.txt
git commit -m "test"
# Should be blocked by hook
```

## Checklist: Before Making Repo Public

- [ ] Review all files with `git ls-files`
- [ ] Check git history for secrets: `git log -p`
- [ ] Run secrets scanner: `gitleaks detect`
- [ ] Verify `.gitignore` is comprehensive
- [ ] Ensure no `client_secret*.json` in history
- [ ] Confirm no API keys in code
- [ ] Remove all `token.*` files
- [ ] Sanitize example files (use placeholders)
- [ ] Review all README examples for hardcoded values
- [ ] Test clone in fresh directory to verify nothing sensitive is included

## Additional Resources

- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_CheatSheet.html)
- [Google Cloud Secret Management](https://cloud.google.com/secret-manager/docs/best-practices)
- [git-secrets (AWS)](https://github.com/awslabs/git-secrets)
- [gitleaks](https://github.com/gitleaks/gitleaks)
