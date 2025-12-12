# TODO: Update User to FamilyMember and Create SQL

- [x] Update models.py: Rename User class to FamilyMember, change __tablename__ to "family_members", update association tables and relationships
- [x] Update routers/users.py: Change User to FamilyMember in imports and code
- [x] Update auth.py: Change User to FamilyMember if referenced
- [x] Update routers/auth.py: Change User to FamilyMember if referenced
- [x] Update main.py: Change User to FamilyMember if referenced
- [x] Create family_members.sql with PostgreSQL commands for Supabase
