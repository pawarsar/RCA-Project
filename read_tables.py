import psycopg2
from psycopg2.extras import RealDictCursor

def read_all_tables():
    tables = [
        "agent_outputs",
        "final_reports",
        "system_prompts"
    ]
    
    conn = None
    try:
        # 1. Connect to the database
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="pawar06"
        )
        
        # Use RealDictCursor to get results as dictionaries (easier to read)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 2. Set search path to your schema
        cur.execute("SET search_path TO rca_db;")
        
        print("--- DATABASE SCHEMA: rca_db ---\n")

        for table in tables:
            print(f"--- Table: {table} ---")
            try:    
                # 3. Retrieve first 5 rows from the table
                # if table == "habitat_features" or table == "habitat_rows" or table == "habitat_segmentation":
                #     cur.execute(f"SELECT * FROM {table} WHERE segmentation_id='2e3b611c-7e0a-4b40-9a7f-798c498485c8' LIMIT 50;")
                # elif table == "sites" or table == "users":
                #     cur.execute(f"SELECT * FROM {table};")
                # else:
                #     cur.execute(f"SELECT * FROM {table} WHERE run_id='2e3b611c-7e0a-4b40-9a7f-798c498485c8' LIMIT 50;")
                rows = cur.fetchall()
                
                if not rows:
                    print("[Empty Table]")
                # else:
                for row in rows:
                    print(row)
                print("\n")
                
            except Exception as e:
                print(f"Error reading {table}: {e}\n")
                conn.rollback() # Rollback if one table fails so we can continue

    except Exception as e:
        print(f"General Connection Error: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    read_all_tables()
