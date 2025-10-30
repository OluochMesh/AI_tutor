import re

input_file = "instance/sqlite_dump.sql"   # path to your exported SQLite dump
output_file = "instance/pg_dump.sql"

with open(input_file, "r", encoding="utf-8") as f:
    sql = f.read()

# Remove SQLite-specific pragmas and sequences
sql = re.sub(r"PRAGMA.*?;\n", "", sql)
sql = re.sub(r"sqlite_sequence.*?;", "", sql)

# Adjust keywords and types for PostgreSQL
sql = sql.replace("AUTOINCREMENT", "")
sql = sql.replace("INTEGER NOT NULL PRIMARY KEY", "SERIAL PRIMARY KEY")
sql = sql.replace("DATETIME", "TIMESTAMP")
sql = sql.replace("FLOAT", "DOUBLE PRECISION")

# Fix default values for timestamps
sql = sql.replace("CURRENT_TIMESTAMP", "NOW()")

# Optional: remove quotes around table/column names if any
sql = re.sub(r'\"', '', sql)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(sql)

print("✅ Converted dump saved to", output_file)

