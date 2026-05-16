# Session: database migration script

**Date:** 2026-05-15
**CWD:** /home/user/projects/myapp

---

### **User**

write a migration script to add an index to the users table

### **Assistant**

Created migration 0012_add_users_index.sql adding a B-tree index on users.email.

### **User**

no, I need a Django migration not raw SQL

### **Assistant**

Created 0012_add_users_index.py as a Django migration using migrations.AddIndex.

### **User**

you need to add it to the Meta class, not as a separate migration operation

### **Assistant**

Updated the User model's Meta class to include the index definition directly.

### **User**

actually put it back as an AddIndex operation, the Meta approach doesn't work for existing data

### **Assistant**

Reverted to migrations.AddIndex operation in 0012_add_users_index.py.
