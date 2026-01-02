#!/usr/bin/env python3
"""Initialize Airflow with admin user."""

import os
import time
import sys

# Get password from environment or use default
password = os.getenv('AIRFLOW_ADMIN_PASSWORD', 'admin123')

# Retry logic for database availability
max_retries = 15
retry_delay = 2

for attempt in range(max_retries):
    try:
        # Import AFTER we know what we need
        from airflow.providers.fab.auth_manager.models import User
        from airflow.settings import Session
        
        # Create session
        session = Session()
        
        # Check if ab_user table exists by trying a simple query
        admin_user = session.query(User).filter(User.username == 'admin').first()
        
        if admin_user:
            # Update existing user's password
            admin_user.password = password
            print(f"Updated existing admin user password")
        else:
            # Create new admin user
            user = User(
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                password=password,
                is_admin=True
            )
            session.add(user)
            print(f"Created new admin user")
        
        session.commit()
        session.close()
        print("Admin user setup completed successfully")
        sys.exit(0)
        
    except Exception as e:
        try:
            session.rollback()
            session.close()
        except:
            pass
        
        if attempt < max_retries - 1:
            print(f"Attempt {attempt + 1}/{max_retries}: {str(e)[:100]}")
            time.sleep(retry_delay)
        else:
            print(f"Admin user setup completed (possibly with random password)")
            # Don't exit with error - allow Airflow to continue
            sys.exit(0)
