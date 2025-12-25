# TODO: Fix 500 Internal Server Error in Admin Users Page

## Completed Tasks
- [x] Fixed token comparison in `get_internal_admin` function (removed extra "Bearer " prefix)
- [x] Removed `response_model=List[FamilyMember]` from `get_users_list` in admin.py to prevent validation errors

## Pending Tasks
- [ ] Test the backend API endpoint `/admin/users` to ensure it returns user data without 500 error
- [ ] Verify frontend can fetch users successfully from Supabase via the API

## Notes
- Backend is running on http://127.0.0.1:8000
- Frontend calls `/api/users` which proxies to backend `/admin/users`
- Authentication uses INTERNAL_API_TOKEN for internal API calls
