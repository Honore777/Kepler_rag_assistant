# Kepler College RAG Assistant - Setup Guide

## Quick Setup

### 1. Create Admin User (Run once)

```bash
cd backend
python scripts/create_admin.py admin@keplercollege.ac.rw "your-password"
```

This creates an admin user with full access to:
- Upload documents
- Activate/deactivate documents
- Invite staff and board members

### 2. User Flows

**Students:**
1. Visit landing page
2. Click "Register" 
3. Use institutional email (@keplercollege.ac.rw)
4. Auto-redirected to **Chat** after login
5. Ask questions about policies, handbooks, etc.

**Admin:**
1. Login with admin credentials
2. Auto-redirected to **Admin Dashboard**
3. Sidebar navigation:
   - Overview (stats)
   - Documents (upload, activate/deactivate)
   - Manage Users (view all users)
   - Send Invites (invite staff/board)

**Staff/Board Members:**
1. Receive invite link from admin
2. Register with invite code
3. Login → **Chat** (with access to more documents)

### 3. Navigation

**Header (when logged in):**
- Home
- Chat
- Admin (only for admin role)
- Username | Logout

**No public access to:**
- Documents page (only in admin dashboard)
- Student records (only in admin dashboard)
- User management (only in admin dashboard)

## Security

- Admin can ONLY be created via script (not public registration)
- Students register with institutional email only
- Staff/Board need invite code from admin
- All auth uses HttpOnly cookies (no localStorage tokens)
- Rate limiting on all public endpoints

## File Structure

```
frontend/
  pages/
    chat.tsx          # Protected - requires login
    auth/login.tsx    # Public - redirects to chat or admin
    auth/register.tsx # Public - creates students only
    admin/dashboard.tsx # Protected - admin only

backend/
  scripts/create_admin.py  # Create admin user
  app/api/auth.py          # Login, register (IP rate limited)
```
