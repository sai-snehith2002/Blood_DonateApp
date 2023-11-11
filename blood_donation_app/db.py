import psycopg2
import os

def create_connection():
    hostname = 'localhost'
    database = 'blood_donationDrive'
    username = os.getenv('DB_USERNAME')
    pwd = os.getenv('DB_PASSWORD')
    port_id = 5432
    
    conn = None
    try:
        conn = psycopg2.connect(
            host=hostname,
            dbname=database,
            user=username,
            password=pwd,
            port=port_id
        )
        return conn

    except Exception as error:
        print(error)
        if conn is not None:
            conn.close()
        return None
