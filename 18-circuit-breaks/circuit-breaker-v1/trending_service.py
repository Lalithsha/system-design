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


@app.route("/trending")
def trending():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status
        FROM service_status
        WHERE service_name = 'profile'
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    status = row[0]

    if status == "UP":

        response = requests.get(
            "http://localhost:5001/profile/1"
        )

        profile = response.json()

        return jsonify({
            "source": "profile-service",
            "profile": profile,
            "trendingPosts": [
                "Post A",
                "Post B",
                "Post C"
            ]
        })

    else:

        return jsonify({
            "source": "fallback",
            "profile": None,
            "trendingPosts": [
                "Global Trending 1",
                "Global Trending 2"
            ]
        })


app.run(
    host="0.0.0.0",
    port=5003,
    debug=True
)