# Setting Up Social Media APIs for MediaMon

This guide will help you set up the social media API integrations for the MediaMon application.

## Twitter API Setup

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new Project and App if you don't have one already
3. Apply for Elevated access (required for search functionality)
4. From your app settings, generate Access Token & Secret
5. Add the following to your `.env` file:
   ```
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_secret
   ```

## Facebook Setup

The app uses `facebook-scraper` which requires a Facebook account to log in:

1. Create a Facebook account or use an existing one
2. Add the following to your `.env` file:
   ```
   FACEBOOK_EMAIL=your_facebook_email
   FACEBOOK_PASSWORD=your_facebook_password
   ```

**Note:** Facebook may block automated logins. If your account gets temporary restrictions:
- Use a dedicated account for this purpose
- Consider using Facebook's Graph API instead (requires app approval)

## Instagram Setup

The app uses `instaloader` which requires an Instagram account for full functionality:

1. Create an Instagram account or use an existing one
2. Add the following to your `.env` file:
   ```
   INSTAGRAM_USERNAME=your_instagram_username
   INSTAGRAM_PASSWORD=your_instagram_password
   ```

**Note:** Instagram may temporarily block automated logins. Using a dedicated account is recommended.

## Loading Environment Variables

### For Local Development
```bash
# Install python-dotenv
pip install python-dotenv

# Create your .env file
cp .env.example .env

# Edit your .env file with your credentials
nano .env
```

### For Firebase Functions
Firebase Functions uses environment configuration in the Firebase Console:

1. Go to the Firebase Console > Functions > Configuration
2. Add all the environment variables from your .env file
3. Deploy your functions with `firebase deploy --only functions`

## Troubleshooting Social Media APIs

### Twitter
- If searches return errors, verify your API keys and make sure you have Elevated access
- Rate limits: Standard access is limited to 500,000 tweets per month

### Facebook
- If login fails, check your credentials and try again
- Facebook may temporarily block automated access; wait 24 hours before trying again

### Instagram
- Login issues may occur if Instagram detects automation
- Try using a dedicated account with 2FA disabled
- If blocked, wait 24-48 hours before attempting again
