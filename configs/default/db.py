import os

import pymysql

if os.getenv("DJANGO_ENV") != "ci":
    # mysql 设置
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "sspanel",
            "PASSWORD": os.getenv("MYSQL_PASSWORD", "yourpass"),
            "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "USER": os.getenv("MYSQL_USER", "root"),
            "OPTIONS": {
                "autocommit": True,
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "charset": "utf8mb4",
            },
        }
    }

    pymysql.install_as_MySQLdb()
