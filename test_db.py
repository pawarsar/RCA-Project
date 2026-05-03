import psycopg2
from database import init_db, engine

print("Running database.init_db()...")
init_db()

conn = psycopg2.connect(dbname='postgres', user='postgres', password='pawar06', host='localhost', port=5432)
cur = conn.cursor()

cur.execute("SHOW search_path;")
print("Current search_path:", cur.fetchone()[0])

cur.execute("SELECT schemaname, tablename FROM pg_tables WHERE tablename='agent_outputs';")
print("Tables found:", cur.fetchall())

cur.execute("SELECT COUNT(*) FROM rca_db.agent_outputs;")
print("Count in rca_db.agent_outputs:", cur.fetchone()[0])
