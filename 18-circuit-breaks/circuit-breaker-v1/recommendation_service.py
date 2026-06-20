from flask import Flask, jsonify
import requests
import psycopg2

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="password",
        database="circuitdb"
    )


@app.route("/recommendations/<user_id>")
def recommendations(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT status
        FROM service_status
        WHERE service_name='profile'
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    status=row[0]

    if status == "UP":
        response = requests.get(f"http://localhost:5001/profile/${user_id}")
        profile = response.json()
        return jsonify({
            "source":"profile-service",
            "profile":profile,
            "recommendations":[
                "Post 1",
                "Post 2"
            ]
        })

    else :

        return jsonify({
            "source":"profile",
            "profile": None,
            "recommendations":[]
        })

app.run(
    host="0.0.0.0",
    port=5002,
    debug=True
)










