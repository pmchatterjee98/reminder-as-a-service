# RAAS Setup Guide

## Required Environment Variables

RAAS uses several environment variables for authentication, notifications, and AI features. Here's how to set them up:

### 1. Email Magic Link Authentication

**SENDER_EMAIL** - Gmail address for sending magic link emails
- **How to get it**: Use your Gmail address (e.g., `yourname@gmail.com`)
- **Where to set it**: Replit Secrets (Tools → Secrets)

**SENDER_PASSWORD** - Gmail app-specific password
- **How to get it**:
  1. Go to https://myaccount.google.com/security
  2. Enable 2-Step Verification if not already enabled
  3. Go to https://myaccount.google.com/apppasswords
  4. Select "Mail" and "Other (Custom name)"
  5. Enter "RAAS" as the name
  6. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)
  7. Remove spaces when entering: `xxxxxxxxxxxxxxxx`
- **Where to set it**: Replit Secrets

**SESSION_SECRET** - Secret key for session tokens
- **How to get it**: Generate a random string (or let RAAS auto-generate in dev mode)
- **Generate one**: Run in Shell: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Where to set it**: Replit Secrets
- **Note**: Auto-generated in development if not set

**ENCRYPTION_KEY** - Fernet key for encrypting contact data
- **How to get it**: Generate a Fernet key
- **Generate one**: Run in Shell: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- **Where to set it**: Replit Secrets
- **Note**: Auto-generated in development if not set

### 2. API Authentication (Optional for REST API)

**RAAS_API_KEY** - Authentication key for REST API
- **How to get it**: Generate a random string
- **Generate one**: Run in Shell: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Where to set it**: Replit Secrets
- **Note**: Optional in development, required in production

### 3. Notification Services (Optional)

**TWILIO_ACCOUNT_SID** - Twilio account identifier for SMS/WhatsApp
- **How to get it**:
  1. Sign up at https://www.twilio.com
  2. Get free trial credits
  3. Find SID on dashboard (starts with `AC`)
- **Where to set it**: Replit Secrets

**TWILIO_AUTH_TOKEN** - Twilio authentication token
- **How to get it**: Find on Twilio dashboard (next to Account SID)
- **Where to set it**: Replit Secrets

**TWILIO_PHONE_NUMBER** - Twilio phone number for SMS
- **How to get it**:
  1. Get a free trial number from Twilio
  2. Format: `+1234567890`
- **Where to set it**: Replit Secrets

### 4. AI Features (Optional but Recommended)

**OPENAI_API_KEY** - OpenAI API key for AI intelligence
- **How to get it**:
  1. Go to https://platform.openai.com/api-keys
  2. Sign in or create an account
  3. Click "Create new secret key"
  4. Copy the key (starts with `sk-`)
- **Where to set it**: Replit Secrets
- **Cost**: Charged per API call at OpenAI's rates
- **Features enabled**: Natural language task creation, auto-categorization, smart scheduling, productivity insights, AI chat

## How to Set Environment Variables in Replit

### Method 1: Using the Secrets Tool (Recommended)

1. Open your Replit workspace
2. Click "Tools" in the left sidebar
3. Select "Secrets"
4. Click "New Secret"
5. Enter the secret name (e.g., `SENDER_EMAIL`)
6. Enter the value
7. Click "Add Secret"
8. Repeat for all required secrets

### Method 2: Using Search Bar

1. Type "Secrets" in the search bar at the top
2. Click on "Secrets" tool
3. Follow the same steps as Method 1

## Quick Setup Checklist

### Minimum Setup (Required)
- [ ] SENDER_EMAIL - Your Gmail address
- [ ] SENDER_PASSWORD - Gmail app-specific password

### Recommended Setup
- [ ] SESSION_SECRET - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] ENCRYPTION_KEY - Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- [ ] OPENAI_API_KEY - For AI features

### Optional Setup
- [ ] RAAS_API_KEY - For REST API access
- [ ] TWILIO_ACCOUNT_SID - For SMS notifications
- [ ] TWILIO_AUTH_TOKEN - For SMS notifications
- [ ] TWILIO_PHONE_NUMBER - For SMS notifications

## Production Deployment

When deploying to production (Replit Publishing or other platforms):

1. **MUST SET**:
   - SENDER_EMAIL
   - SENDER_PASSWORD
   - SESSION_SECRET (strong random value)
   - ENCRYPTION_KEY (strong random value)
   - RAAS_API_KEY (strong random value)

2. **Enable HTTPS**: Required to protect session tokens (automatic on Replit)

3. **Verify Settings**: Check that all environment variables are set in the production environment

## Testing Your Setup

After setting environment variables:

1. **Restart the app**: Click the restart button in Replit
2. **Test login**: Go to your app URL and request a magic link
3. **Check email**: Verify you receive the magic link email
4. **Test AI**: Try creating a task with natural language (if OpenAI API key is set)

## Troubleshooting

**Magic links not sending?**
- Verify SENDER_EMAIL and SENDER_PASSWORD are correct
- Check Gmail app password is properly formatted (no spaces)
- Ensure 2-Step Verification is enabled on Gmail

**Session errors?**
- SESSION_SECRET is automatically generated in dev mode
- Set it explicitly for production

**Encryption errors?**
- ENCRYPTION_KEY is automatically generated in dev mode
- Set it explicitly for production

**AI features not working?**
- Verify OPENAI_API_KEY is set correctly
- Check OpenAI account has available credits
- AI features are optional - RAAS works without them

## Security Best Practices

1. **Never commit secrets to code**
2. **Use strong random values** for SESSION_SECRET, ENCRYPTION_KEY, and RAAS_API_KEY
3. **Rotate keys periodically** in production
4. **Use HTTPS** (automatic on Replit Publishing)
5. **Monitor API usage** for OpenAI and Twilio to control costs

## Support

For questions or issues:
- Check the logs in Replit console
- Verify all environment variables are set
- Ensure Gmail app password is correct
- Contact support if issues persist
