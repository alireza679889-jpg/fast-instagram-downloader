# Fast Instagram Downloader

A production-grade Telegram bot for downloading Instagram Reels, built with Cloudflare Workers and GitHub Actions.

## 🎯 Features

- **Telegram Bot Integration**: Send Instagram Reel URLs directly via Telegram
- **Cloudflare Workers**: Serverless webhook handler (free tier available)
- **GitHub Actions**: Automated reel download and upload
- **yt-dlp Integration**: Reliable Instagram media extraction
- **Production Ready**: Clean, modular, scalable architecture
- **Zero Cost**: Runs entirely on free tiers of GitHub, Cloudflare, and Telegram

## 📋 System Architecture

```
User Message
     ↓
Telegram Bot
     ↓
Cloudflare Worker (Webhook)
     ↓
URL Validation & Parse
     ↓
GitHub Actions Trigger
     ↓
yt-dlp Download
     ↓
Telegram API Upload
     ↓
User Receives Reel
```

## 🚀 Quick Start

### Prerequisites

- GitHub account with repository access
- Cloudflare account (free tier)
- Telegram Bot Token (get from @BotFather)
- Personal GitHub Token with `repo` and `workflow` permissions

### 1. Repository Setup

```bash
# Clone or use the provided structure
git clone https://github.com/alireza679889-jpg/fast-instagram-downloader.git
cd fast-instagram-downloader

# Install dependencies
npm install
```

### 2. Configure Secrets

**GitHub Repository Secrets** (`Settings > Secrets and variables > Actions`):

```
BOT_TOKEN              # Your Telegram Bot Token
GITHUB_TOKEN           # Your Personal GitHub Token
REPO_OWNER             # Your GitHub username
REPO_NAME              # Repository name (fast-instagram-downloader)
```

**Cloudflare Secrets** (in `wrangler.toml` or via CLI):

```bash
wrangler secret put BOT_TOKEN
wrangler secret put GITHUB_TOKEN
wrangler secret put REPO_OWNER
wrangler secret put REPO_NAME
```

### 3. Deploy Cloudflare Worker

```bash
# Login to Cloudflare
wrangler login

# Deploy to production
wrangler deploy --env production

# Or deploy to staging
wrangler deploy --env staging
```

After deployment, you'll get a URL like: `https://fast-instagram-downloader-prod.workers.dev`

### 4. Configure Telegram Webhook

```bash
# Set webhook URL with your Cloudflare worker URL
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://fast-instagram-downloader-prod.workers.dev/webhook"}'

# Verify webhook
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

## 📁 Project Structure

```
fast-instagram-downloader/
├── src/
│   ├── index.js              # Cloudflare Worker entry point
│   ├── config.js             # Configuration management
│   ├── validators.js         # URL and input validation
│   ├── telegram.js           # Telegram Bot API integration
│   ├── instagram.js          # Instagram URL processing
│   └── github.js             # GitHub Actions integration
│
├── downloader/
│   ├── download.py           # Main download script
│   └── requirements.txt       # Python dependencies
│
├── .github/workflows/
│   └── downloader.yml        # GitHub Actions workflow
│
├── wrangler.toml             # Cloudflare Worker config
├── package.json              # NPM dependencies
├── .gitignore
└── README.md
```

## 🔧 Environment Variables

### Cloudflare Worker

```javascript
// Automatically loaded from wrangler.toml secrets
BOT_TOKEN              // Telegram Bot API token
GITHUB_TOKEN           // GitHub Personal Access Token
REPO_OWNER             // GitHub repository owner
REPO_NAME              // Repository name
MAX_RETRIES            // (Optional) Default: 3
REQUEST_TIMEOUT        // (Optional) Default: 30000ms
MAX_FILE_SIZE          // (Optional) Default: 52428800 bytes (50MB)
RATE_LIMIT_ENABLED     // (Optional) Default: true
LOGGING_LEVEL          // (Optional) Default: info
```

### GitHub Actions

Set via Secrets in repository settings:

```
BOT_TOKEN              // Required for sending results to Telegram
GITHUB_TOKEN           // Auto-provided by GitHub
```

## 📤 Usage

### For Users

1. Start a conversation with your bot on Telegram
2. Send an Instagram Reel URL:
   ```
   https://www.instagram.com/reels/ABC123XYZ/
   ```
3. Bot responds with typing indicator
4. GitHub Actions downloads the reel
5. Reel is uploaded back to Telegram

### Supported URL Formats

- `https://instagram.com/reels/ID/`
- `https://www.instagram.com/reels/ID/`
- `https://www.instagram.com/p/ID/` (if it's a reel)

## 🔐 Security

### Best Practices

1. **Never commit secrets** - Use GitHub Secrets and Cloudflare Secrets
2. **Token rotation** - Regenerate tokens periodically
3. **URL validation** - Only Instagram Reel URLs are accepted
4. **Input sanitization** - All user inputs are sanitized before processing
5. **Error handling** - Errors are never exposed to users

### Rate Limiting (Future)

- Per-user rate limits via Cloudflare KV
- Per-minute and per-hour thresholds
- Graceful backoff notifications

## 📊 Workflow Details

### Cloudflare Worker Flow

```
POST /webhook
  ↓
Parse Telegram update
  ↓
Extract message text
  ↓
Validate Instagram URL
  ↓
Create download job
  ↓
Trigger GitHub Actions
  ↓
Return 200 OK
```

### GitHub Actions Flow

```
Workflow triggered
  ↓
Checkout code
  ↓
Install Python 3.11
  ↓
Install yt-dlp
  ↓
Download reel from URL
  ↓
Upload to Telegram
  ↓
Clean temporary files
  ↓
Report errors (if any)
```

## 🧪 Testing

### Local Development

```bash
# Start Cloudflare Worker locally
wrangler dev

# In another terminal, test health endpoint
curl http://localhost:8787/health

# Output:
# {"status":"healthy","timestamp":"2024-12-16T..."}
```

### Test Webhook Locally

```bash
# Mock Telegram update
curl -X POST http://localhost:8787/webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "update_id": 123456789,
    "message": {
      "message_id": 1,
      "from": {"id": 987654321, "is_bot": false},
      "chat": {"id": 987654321},
      "date": 1700000000,
      "text": "https://www.instagram.com/reels/ABC123XYZ/"
    }
  }'
```

### GitHub Actions Manual Trigger

```bash
# Trigger workflow manually
gh workflow run downloader.yml \
  -f reel_url="https://www.instagram.com/reels/ABC123XYZ/" \
  -f chat_id="987654321" \
  -f user_id="987654321" \
  -f message_id="1" \
  -f job_id="job_1234567890"
```

## 🐛 Troubleshooting

### Webhook Not Receiving Updates

```bash
# Check webhook status
curl https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo

# Verify worker is accessible
curl https://fast-instagram-downloader-prod.workers.dev/health
```

### Download Failing

1. Check GitHub Actions logs: `Actions > downloader.yml > Latest run`
2. Verify Instagram URL is public and not age-restricted
3. Check yt-dlp version: `yt-dlp --version`
4. Verify BOT_TOKEN is correct in secrets

### Telegram Error Messages

- **Invalid URL**: URL doesn't match Instagram Reel format
- **Download failed**: yt-dlp couldn't extract the reel
- **Upload failed**: File size exceeds Telegram limit (50MB) or network issue

## 📈 Performance

- **Worker Response Time**: < 100ms (usually instant)
- **Download Time**: 10-60 seconds (depends on video size and internet)
- **Upload Time**: 10-30 seconds (depends on file size)
- **Total Flow**: ~30-120 seconds from user message to receipt

## 🛣️ Future Roadmap

### Phase 1: MVP (Current)
- ✅ Instagram Reels download
- ✅ Telegram Bot integration
- ✅ GitHub Actions automation

### Phase 2: Enhancements
- [ ] Rate limiting (Cloudflare KV)
- [ ] User analytics
- [ ] Admin commands
- [ ] Forced channel join
- [ ] Ad integration
- [ ] Caching layer

### Phase 3: Expansion
- [ ] Instagram Stories support
- [ ] Instagram Posts support
- [ ] Instagram Carousel support
- [ ] TikTok support
- [ ] YouTube Shorts support
- [ ] Database (free tier)

### Phase 4: Scale
- [ ] Multi-language support
- [ ] Multiple bots
- [ ] Admin dashboard
- [ ] User statistics
- [ ] Premium features

## 💰 Cost Analysis

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| Cloudflare Workers | Free | $0 | 100k req/day |
| GitHub Actions | Free | $0 | 2000 min/month |
| Telegram Bot API | Free | $0 | No limits |
| **Total** | | **$0** | Completely free |

## 📝 API Reference

### Telegram Webhook Payload

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "John"
    },
    "chat": {
      "id": 987654321,
      "type": "private"
    },
    "date": 1700000000,
    "text": "https://www.instagram.com/reels/ABC123XYZ/"
  }
}
```

### GitHub Workflow Trigger

```json
{
  "reel_url": "https://www.instagram.com/reels/ABC123XYZ/",
  "chat_id": "987654321",
  "user_id": "987654321",
  "message_id": "1",
  "job_id": "job_1234567890",
  "timestamp": "2024-12-16T10:30:00Z"
}
```

## 🤝 Contributing

This is a personal project, but feel free to fork and customize for your needs.

## 📄 License

MIT License - See LICENSE file

## ⚠️ Disclaimer

This tool is for personal use. Respect Instagram's Terms of Service and local copyright laws when downloading content.

---

**Built with ❤️ using Cloudflare Workers, GitHub Actions, and Telegram Bot API**
