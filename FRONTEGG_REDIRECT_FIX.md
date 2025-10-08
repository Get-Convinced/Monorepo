# 🔧 Frontegg Redirect URL Fix

## ❌ Problem
After Google OAuth login, Frontegg returns:
```json
{"errors":["The requested URL was not found on this server."]}
```

## ✅ Solution
Add these redirect URLs in Frontegg Dashboard:

### Development URLs (localhost)
```
http://localhost:3000
http://localhost:3000/
http://localhost:3000/oauth/callback
http://localhost:3000/login
```

### Production URLs
```
https://your-production-domain.com
https://your-production-domain.com/
https://your-production-domain.com/oauth/callback
https://your-production-domain.com/login
```

## 📍 Where to Add These

### Location 1: Hosted Login Configuration
1. Go to: https://portal.frontegg.com
2. Select your app
3. Navigate to: **Authentication → Login Method → Hosted Login**
4. Find: **"Redirect URLs"** section
5. Add all URLs listed above
6. Click **"Save"**

### Location 2: Google Social Login
1. Navigate to: **Authentication → Social Logins → Google**
2. Find: **"Redirect URIs"** section
3. Add the same URLs again
4. Ensure **"Enabled"** is checked
5. Click **"Save"**

### Location 3: Allowed Origins
1. Navigate to: **Settings → Domains**
2. Add:
   - `http://localhost:3000` (for local development)
   - `https://your-production-domain.com` (for production)
3. Click **"Save"**

## 🔍 Verification

After adding the URLs:

1. **Clear browser cache** (or use incognito mode)
2. Restart your frontend:
   ```bash
   cd apps/frontend
   pnpm run dev
   ```
3. Try logging in with Google again
4. You should be redirected to `http://localhost:3000` successfully

## 🎯 Expected Flow

```
User clicks "Sign in with Google"
        ↓
Google authenticates user
        ↓
Redirects to: https://app-griklxnnsxag.frontegg.com/account/social/success
        ↓
Frontegg processes authentication
        ↓
Redirects to: http://localhost:3000 ✅
        ↓
Your Next.js middleware handles session
        ↓
User sees dashboard
```

## 🚨 Common Mistakes

❌ **Mistake 1:** Only adding URLs to one location
✅ **Fix:** Add URLs to ALL three locations (Hosted Login, Social Login, Domains)

❌ **Mistake 2:** Forgetting the trailing slash `/`
✅ **Fix:** Add both `http://localhost:3000` AND `http://localhost:3000/`

❌ **Mistake 3:** Not saving after adding URLs
✅ **Fix:** Click "Save" button after each change

❌ **Mistake 4:** Old cached session
✅ **Fix:** Clear browser cache or use incognito mode

## 📞 Need Help?

If still not working, check:
1. Frontegg logs: https://portal.frontegg.com → Logs
2. Browser console: F12 → Console tab
3. Network tab: F12 → Network tab → Check redirect URLs

---

Last Updated: January 2025

