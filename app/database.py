import psycopg2
from psycopg2.extras import RealDictCursor



try:
    dbconn = psycopg2.connect(host='localhost', database='PCE', user='postgres', password='root', cursor_factory=RealDictCursor)
    cursor = dbconn.cursor()
    print("DATABASE CONNECTION ESTABLISHED")
except Exception as e:
    print(f"DATABASE CONNECTION FAILED: {e}")
