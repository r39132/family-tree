# Family Spaces Implementation - Setup Guide

This document describes how to complete the family spaces setup for the family-tree application.

## ✅ What's Already Implemented

1. **Backend Space Scoping**: All routes now support family spaces
   - Tree operations (members, relations, moves, spouse operations)
   - Events and notifications (space-scoped)
   - Invites (space-scoped)
   - Authentication with space selection

2. **Frontend Integration**:
   - Login page with family space dropdown
   - TopNav with current space display and space switcher

3. **Space Management**: Complete CRUD API for family spaces

4. **Test Compatibility**: All tests pass with space scoping

## 🚀 Next Steps to Complete Setup

### 1. Set Up Firestore Database

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (family-tree-469815)
3. Navigate to Firestore Database
4. Create a Firestore database in Native mode
5. Set up a service account key and download the JSON file
6. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

### 2. Run Migration Scripts

Once your database is set up, run these scripts to set up the data:

#### A. Migrate existing data to demo space:
```bash
cd backend
python migrate_to_spaces.py
```

This will:
- Create the "demo" family space
- Move all existing members to demo space
- Move all existing relations to demo space
- Update all existing users to use demo space
- Migrate invites and event notifications

#### B. Seed family spaces and admin user:
```bash
cd backend
python seed_spaces.py
```

This will:
- Create all family spaces (demo, karunakaran, anand, kullatira)
- Create admin user "sanand" with email sanand@apache.org
- Set up initial members for the admin in each space

### 3. Test the Implementation

1. Start the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Test login with space selection:
   - Visit http://localhost:3000/login
   - You should see a dropdown with family spaces
   - Login with existing users (they'll be in demo space)
   - Login with sanand@apache.org / admin123 to test other spaces

4. Test space switching:
   - After login, the TopNav should show current space
   - Click on the space name to see space switcher
   - Switch between spaces and verify data isolation

## 🎯 Expected Behavior

### For Existing Users:
- All existing data will be in "Demo Family" space
- Existing users can continue using the app normally
- They can switch to other spaces if they have access

### For New Spaces:
- Admin user "sanand" has access to karunakaran, anand, and kullatira spaces
- Each space is completely isolated (separate members, relations, events, invites)
- Invites created in one space only work for that space
- Events and notifications are space-specific

### Admin Features:
- Only admin users can create/delete spaces (through API)
- Admin users can switch between any spaces they have access to
- Regular users can only access spaces they're invited to

## 🔧 Configuration

The spaces are defined in the seed script as:
- **demo**: Demo Family (existing data)
- **karunakaran**: Karunakaran Family
- **anand**: Anand Family
- **kullatira**: Kullatira Family

The admin user credentials are:
- Username: sanand
- Email: sanand@apache.org
- Password: admin123 (should be changed after first login)

## 📚 API Changes

All endpoints now support space scoping:

### Tree Operations:
- GET /tree - Returns tree for current user's space
- All member operations scoped to current space
- All relation operations scoped to current space

### Events:
- GET /events - Returns events for current user's space
- Event notifications are space-specific

### Invites:
- POST /auth/invite - Creates invites for current space
- GET /auth/invites - Lists invites for current space
- Invites can only be redeemed for their associated space

### Space Management:
- GET /spaces - List spaces user has access to
- POST /spaces - Create new space (admin only)
- DELETE /spaces/{space_id} - Delete space (admin only)
- POST /auth/switch-space - Switch user's current space

## 🐛 Troubleshooting

### Database Issues:
- Make sure Firestore is set up in Google Cloud Console
- Verify GOOGLE_APPLICATION_CREDENTIALS is set correctly
- Check that your service account has Firestore permissions

### Migration Issues:
- Run migration scripts only after database is set up
- Check that existing data exists before running migration
- Migration scripts are idempotent (safe to run multiple times)

### Space Access Issues:
- Users can only see spaces they have access to
- Default fallback is always "demo" space
- Check user's current_space field in Firestore

## 🎉 Success Criteria

You'll know the implementation is working when:

1. ✅ Login page shows family space dropdown
2. ✅ TopNav displays current space name
3. ✅ Users can switch between spaces
4. ✅ Data is isolated between spaces (different members/events per space)
5. ✅ Invites work correctly for each space
6. ✅ Admin user can access all non-demo spaces
7. ✅ Existing users see their data in demo space

## 📝 Future Enhancements

Potential improvements for later:
- Space permissions system (read-only access, etc.)
- Space invitation system (invite users to existing spaces)
- Space statistics and analytics
- Bulk data migration between spaces
- Space-specific themes and customization
