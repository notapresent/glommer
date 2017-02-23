Requirements
============

PostgreSQL >= 9.4
python >= 3.4


Configuration
=============

All configuration is done via environment variables. You **must** define all required variables.

Required settings
-----------------

| Variable | Description |
 --- | --- |
| `DATABASE_URL`    | Database connection string. For example, `postgres://user:password@host:post/database_name` |
| `SECRET_KEY`      | Key, used to provide cryptographic signing. Should be set to a unique, unpredictable value.
| `ALLOWED_HOSTS`   | A string or list of comma-separated strings representing the domain names that this app serves

Optional settings
-----------------

`DEBUG`
