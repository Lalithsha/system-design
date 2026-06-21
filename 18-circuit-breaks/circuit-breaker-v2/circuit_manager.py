from flask import Flask
import psycopg2
import redis

app = Flask(__name__)

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="password",
        database="circuitdb"
    )


@app.route("/profile/down")
def profile_down():

    conn = get_db_connection()
    cursor= conn.cursor()


    cursor.execute("""
        UPDATE service_status
        SET status='DOWN'
        WHERE service_name='profile'
    """)

    conn.commit()

    cursor.close()
    conn.close()


    r.publish(
        "circuit_updates",
        "profile:DOWN" 
    )

    return "Profile marked DOWN"


@app.route("/profile/up")
def profile_up():

    conn= get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE service_status
        SET status='UP'
        WHERE service_name='profile'
    """)

    conn.commit()

    cursor.close()
    conn.close()

    r.publish(
        "circuit_updates",
        "profile:UP"
    )

    return "Profile marked UP"


app.run(
    host="0.0.0.0",
    port=5004,
    debug=True
)    



















