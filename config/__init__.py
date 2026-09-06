# If DB_ENGINE=mysql (e.g. on PythonAnywhere, which offers MySQL but not
# Postgres out of the box), use the pure-Python PyMySQL driver instead of
# mysqlclient — mysqlclient needs to compile a C extension against MySQL's
# dev headers, which isn't available on PythonAnywhere's free/Hacker plans.
# This has zero effect when running against Postgres or SQLite.
from decouple import config

if config('DB_ENGINE', default='postgresql') == 'mysql':
    import pymysql
    pymysql.install_as_MySQLdb()
