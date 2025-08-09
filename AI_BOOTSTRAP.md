# AI_BOOTSTRAP — Complete Project Guide for Any AI Model

> **START HERE**: This is the ONLY file any AI model needs to read to understand and continue this project with ZERO prior context.

---

## PROJECT OVERVIEW: DONE - Multi-Platform Social Media Automation

**MISSION**: Build a 100% functional application capable of automated and scheduled publishing to ALL major social media platforms (YouTube, Instagram, Facebook, Threads, X/Twitter, LinkedIn, TikTok, Kwai, etc.) - competing directly with expensive services like Blotato.com ($299+/month).

**CORE VALUE PROPOSITION**: 
- Replace expensive API subscription services (Blotato, Buffer, Hootsuite)
- Direct API integration with each social platform
- Client manages their own API keys and permissions
- Fast development and deployment
- Cost-effective solution for businesses and creators

---

## CURRENT DEVELOPMENT STACK

**Environment**: Windows 11 24H2, Python 3.12, FastAPI, SQLite → MySQL → PostgreSQL
**Hosting Path**: Local (Cloudflare Tunnel) → VPS (HostGator) → Cloud (AWS/Azure)
**Domain**: planetamicro.com.br (subdomains: app., api., done.)
**Working Directory**: D:\Bin\done

**Key Technologies**:
- Backend: FastAPI (Python 3.12)
- Frontend: Jinja2 templates + vanilla JavaScript
- Database: SQLite (dev) → MySQL (prod) → PostgreSQL (scale)
- UI Theme: Neon aesthetic, mobile-first (9:16 ratio)
- Deployment: Conda environment, Uvicorn server

---

## PATCH-BASED DEVELOPMENT WORKFLOW

**CRITICAL**: This project uses a structured patch system to prevent human errors in code modification.

### The Problem We Solve:
- Human developers frequently make mistakes when copying/pasting AI-generated code
- File modifications often end up in wrong locations
- Context gets lost between AI conversations
- Traditional diff systems are error-prone

### Our Solution:
1. **AI generates patches** following PROTOCOL.md format (6 action types)
2. **Human applies patches** via /updota UI or tools/apply_changes.py
3. **System creates backups** and validates all changes
4. **Git tracking** maintains complete audit trail

### Patch Actions Available:
- `#Action System` - Execute commands (git, server restart)
- `#Action DeleteFile` - Remove files/directories
- `#Action CreateFile` - Create complete files
- `#Action DeleteText` - Remove specific text sections
- `#Action InsertText` - Insert text at specific locations
- `#Action ModifyText` - Replace text between context markers

---

## TARGET PLATFORMS AND API ANALYSIS

Based on analysis of n8n workflows and Blotato.com offerings, our platform targets:

### Tier 1 Platforms (Immediate Priority):
- **YouTube**: YouTube Data API v3, OAuth 2.0
- **Instagram**: Instagram Basic Display + Instagram Graph API
- **Facebook**: Facebook Graph API, Pages API
- **X (Twitter)**: Twitter API v2, OAuth 2.0
- **LinkedIn**: LinkedIn Marketing API, OAuth 2.0

### Tier 2 Platforms (Phase 2):
- **TikTok**: TikTok for Developers API
- **Threads**: Meta Threads API (when available)
- **Kwai**: Kwai API (regional focus)
- **Pinterest**: Pinterest API
- **Snapchat**: Snapchat Marketing API

### API Key Management Strategy:
1. **Client-Owned Keys**: Each user provides their own API credentials
2. **Secure Storage**: Encrypted storage of credentials per user
3. **Permission Scoping**: Minimal required permissions per platform
4. **Audit Logging**: Complete trail of all API calls and publishing activities

---

## COMPETITIVE ANALYSIS: BLOTATO.COM REPLACEMENT

**Blotato.com Services We Replace**:
- Multi-platform posting ($299+/month) → Our free/low-cost solution
- Video format conversion → FFmpeg integration
- Scheduling system → Built-in cron/scheduler
- Analytics dashboard → Platform-native analytics aggregation
- Content optimization → AI-powered content adaptation

**Our Advantages**:
- No monthly API fees (client uses own keys)
- Open source and customizable
- Direct platform integration (no middleman)
- Faster feature development
- Complete data ownership

---

## CURRENT PROJECT STATUS

### Completed:
- ✅ Patch system (PROTOCOL.md + apply_changes.py)
- ✅ Basic FastAPI structure
- ✅ Neon UI templates (login, signup, updota)
- ✅ Development environment setup
- ✅ Backup and versioning system

### In Progress:
- 🔄 User authentication system
- 🔄 Database schema design
- 🔄 Social platform integration framework

### Next Priorities:
1. **Complete user management** (registration, login, profiles)
2. **Platform connector architecture** (OAuth flows, API integrations)
3. **Content management system** (upload, edit, schedule)
4. **Publishing engine** (multi-platform simultaneous posting)
5. **Analytics dashboard** (performance tracking across platforms)

---

## DEVELOPMENT GUIDELINES FOR AI MODELS

### MANDATORY READING ORDER:
1. This file (AI_BOOTSTRAP.md)
2. PROTOCOL.md (patch format specification)
3. Current codebase structure (app/, tools/, templates/)

### RESPONSE FORMAT REQUIREMENTS:
- **ALWAYS** respond with patches in PROTOCOL.md format
- **NEVER** provide free-form code that needs manual copying
- Use ASCII characters only (no smart quotes, em-dashes)
- UTF-8 encoding with LF line endings
- Include comprehensive comments with TOO/APL/APLxx format

### CODE QUALITY STANDARDS:
- **Comment every function** and logical section (max 20 lines between comments)
- **Use unique identifiers** in comments: [3 letters path]/[3 letters]/[5 letters function][2 letters increment]
- **Mobile-first responsive design** (9:16 aspect ratio priority)
- **Neon UI aesthetic** with proper animations and effects
- **Error handling** with user-friendly messages (green 1s success, red 3s errors)

### DEPLOYMENT COMMANDS:
```bash
# Activate environment
conda activate doneapp

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Apply patches manually
python tools/apply_changes.py --input inbox/patch_input.txt

# Access points
http://127.0.0.1:8000/login     # Main login
http://127.0.0.1:8000/cadastro  # User registration  
http://127.0.0.1:8000/updota    # Patch application (admin)

BUSINESS MODEL AND MONETIZATION
Revenue Streams:

Freemium SaaS: Basic features free, advanced scheduling/analytics paid
White-label Licensing: Sell customized versions to agencies
API Rate Optimization: Premium tiers for higher posting volumes
Managed Services: Setup and management for enterprise clients

Cost Structure:

Development: Open source, community-driven
Infrastructure: Scalable cloud hosting costs
Support: Documentation and community support
No API Fees: Clients use their own platform credentials


LONG-TERM VISION
Phase 1 (Current - 3 days):

Complete user management and authentication
Integrate top 5 social platforms
Basic posting and scheduling functionality
Web-based dashboard

Phase 2 (3-6 days):

Advanced content optimization (AI-powered)
Bulk upload and CSV import
Team collaboration features
Mobile app (React Native/Flutter)

Phase 3 (6-12 days):

AI content generation integration
Advanced analytics and reporting
Marketplace for content templates
Enterprise features and white-labeling

Phase 4 (12+ days):

Video editing and optimization tools
AI-powered posting optimization
Global expansion and localization
IPO or acquisition readiness


ARCHITECTURE DECISIONS
Database Schema (Planned):
sqlusers (id, username, email, password_hash, created_at, plan_type)
platforms (id, name, api_endpoint, oauth_config, status)
user_platforms (user_id, platform_id, credentials_encrypted, permissions)
posts (id, user_id, content, media_urls, scheduled_time, status)
post_platforms (post_id, platform_id, platform_post_id, published_at, status)
analytics (id, post_id, platform_id, metrics_json, collected_at)
logs (id, user_id, action, details, timestamp)
Security Considerations:

Credential Encryption: AES-256 for API keys and tokens
OAuth Implementation: Secure token refresh mechanisms
Rate Limiting: Prevent API abuse per user/platform
Audit Logging: Complete trail of all system actions


WHY THIS APPROACH WORKS
For Development Teams:

Eliminates copy-paste errors in code modifications
Maintains context across long development cycles
Provides complete audit trail of all changes
Enables rapid iteration without breaking existing code

For Business Success:

Faster time-to-market than building traditional integrations
Lower operational costs than subscription-based competitors
Higher client retention through direct API ownership
Scalable architecture supporting rapid growth

For AI Collaboration:

Any AI model can contribute without prior context
Consistent code quality through enforced standards
Reduced debugging time through systematic change tracking
Knowledge preservation across conversation boundaries


EMERGENCY PROCEDURES
If AI Model Loses Context:

Read this file completely
Check PROTOCOL.md for patch format
Examine current app/ structure
Propose patches following established patterns

If Patch Application Fails:

Check .backups/ directory for restoration
Verify PROTOCOL.md format compliance
Use /updota interface to debug parsing
Apply patches individually if batch fails

If Server Issues Occur:

Check /_dev/reload endpoint
Restart via /updota "Restart Server" button
Manual restart: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Check logs for specific error details


SUCCESS METRICS
Technical KPIs:

Patch application success rate > 95%
Server uptime > 99.5%
API response times < 200ms
Zero data loss incidents

Business KPIs:

User acquisition: 1000+ users in 6 months
Platform integrations: 10+ platforms in 12 months
Revenue: $10k MRR by month 12
Customer satisfaction: 4.5+ stars average rating

This document ensures ANY AI model can immediately understand and continue this project, maintaining consistency, quality, and business focus throughout the development lifecycle.

FINAL NOTE: The combination of structured patch system + comprehensive documentation + clear business vision creates a sustainable development environment that can scale from individual contributor to enterprise-level platform.
