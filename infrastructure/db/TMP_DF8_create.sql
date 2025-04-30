--- ====================================================================================
---                        CREATE TMP_DF8 DATABASE
--- ====================================================================================


-- (run this as superuser or in your Python setup script, NOT inside TMP_DF8.sql)

DROP DATABASE IF EXISTS TMP_DF8;
CREATE DATABASE TMP_DF8
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en-US'
    LC_CTYPE = 'en-US'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;
