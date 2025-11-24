# ngrok Setup Guide for NeuroSight

## Quick Setup (Manual Download)

Since chocolatey requires admin permissions, let's download ngrok manually:

### Step 1: Download ngrok
1. Go to: https://ngrok.com/download
2. Click **"Download for Windows"**
3. Extract the ZIP file to a folder (e.g., `C:\ngrok\`)

### Step 2: Sign up for ngrok (Free)
1. Go to: https://dashboard.ngrok.com/signup
2. Sign up with Google or email (it's free!)
3. After signing in, you'll see your **authtoken**

### Step 3: Authenticate ngrok
Open PowerShell in the folder where you extracted ngrok and run:
```powershell
.\ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

### Step 4: Start ngrok tunnel
Make sure your Flask app is running on port 5000, then run:
```powershell
.\ngrok http 5000
```

You'll see output like:
```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5000
```

### Step 5: Copy your public URL
The **Forwarding** line shows your public URL, for example:
```
https://abc123.ngrok-free.app
```

This URL is accessible from anywhere in the world!

### Step 6: Update Google OAuth
1. Go to Google Cloud Console → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://abc123.ngrok-free.app/auth/google/callback
   ```
   (Replace with your actual ngrok URL)

### Step 7: Access your app
- From anywhere: `https://abc123.ngrok-free.app`
- From your phone: `https://abc123.ngrok-free.app`
- Google OAuth will work perfectly!

---

## Alternative: Use ngrok without installation

If you don't want to download anything, you can use **localhost.run** (no signup needed):

```bash
ssh -R 80:localhost:5000 localhost.run
```

You'll get a URL like: `https://random-name.localhost.run`

---

## Tips

- **Free tier**: ngrok URLs change every time you restart (unless you have a paid plan)
- **Keep it running**: Don't close the ngrok terminal while testing
- **Web Interface**: Visit `http://127.0.0.1:4040` to see request logs
- **Update OAuth**: Remember to update Google Cloud Console with the new URL each time

---

## Quick Commands

**Start ngrok:**
```powershell
cd C:\ngrok
.\ngrok http 5000
```

**Stop ngrok:**
Press `Ctrl+C` in the ngrok terminal

**View logs:**
Open browser: `http://127.0.0.1:4040`
