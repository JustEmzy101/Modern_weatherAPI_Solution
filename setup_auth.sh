#!/bin/bash
# Create the passwords JSON file for SimpleAuthManager

AIRFLOW_HOME=${AIRFLOW_HOME:-/opt/airflow}
PASSWORD_FILE="$AIRFLOW_HOME/simple_auth_manager_passwords.json.generated"
ADMIN_PASSWORD="${AIRFLOW_ADMIN_PASSWORD}"

# Create the password file with the admin user and password
# The file format is: {"username": "password", ...}
cat > "$PASSWORD_FILE" << EOF
{"admin": "$ADMIN_PASSWORD"}
EOF

echo "Created password file at $PASSWORD_FILE"
