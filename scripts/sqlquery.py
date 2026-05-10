import duckdb # type: ignore

conn = duckdb.connect('db/urg_migration.duckdb')

print("Connected to urg_migration.duckdb")
print("Type your SQL and press Enter. Type 'exit' to quit.")
print("")

while True:
    sql = input("SQL> ")
    if sql.lower() == "exit":
        break
    try:
        result = conn.execute(sql).fetchdf()
        print(result.to_string())
        print("")
    except Exception as e:
        print(f"Error: {e}")
        print("")

conn.close()