import time
import redis
import psycopg2



# Redis connection
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

#PostgreSQL connection
pg_conn = psycopg2.connect(host="localhost", port=5432, user="postgres", password="password", database="postgres")

pg_cursor = pg_conn.cursor()

# Redis SET benchmark 
start = time.perf_counter();
redis_client.set('user:1', "lalith")
end = time.perf_counter();
print(f"Redis SET : {(end-start)*1000:.4f} ms")


# Redis GET benchmark
start = time.perf_counter();
redis_client.get("user:1");
end = time.perf_counter();
print(f"Redis GET : {(end-start)*1000:.4f} ms")


# PostgreSQL INSERT
start = time.perf_counter()
pg_cursor.execute("INSERT INTO benchmark(name) VALUES(%s)", ("Lalith",))
pg_conn.commit()
end = time.perf_counter()
print(f"Postgres INSERT: {(end-start)*1000:.4f} ms")


# PostgreSQL GET
start = time.perf_counter();
pg_cursor.execute(""" SELECT * FROM benchmark ORDER BY id DESC LIMIT 1 """)
pg_cursor.fetchone();
end = time.perf_counter()
print(f"Postgres SELECT: {(end-start)*1000:.4f} ms")

pg_cursor.close()
pg_conn.close()




