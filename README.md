Requirements
============

- PostgreSQL >= 9.4
- python >= 3.4


Configuration
=============

All configuration is done via environment variables. You **must** define all required variables. For omitted optional settings sensible defaults will be used.


Required settings
-----------------

| Variable          | Description
|-------------------|------------
| `SECRET_KEY`      | Key, used to provide cryptographic signing. Should be set to a unique, unpredictable value. Only required if `DEBUG` is `False`


Optional settings
-----------------

| Variable          | Description
|-------------------|------------
| `DATABASE_URL`    | Database connection string. Default: `postgresql://glommer:glommer@localhost/glommer`
| `DEBUG`           | Set this to non-empty string to enable debug mode. Turned off by default
| `IP`              | IP address to bind to. Default: `127.0.0.1`
| `PORT`            | port number to listen on. Default: `8080`
| `ALLOWED_HOSTS`   | A string or list of comma-separated strings representing the domain names that this app serves
