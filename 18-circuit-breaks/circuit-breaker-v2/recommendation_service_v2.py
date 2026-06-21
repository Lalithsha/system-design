from flask import Flask, jsonify, request
import requests
import psycopg2
import redis
import threading


app = Flask(__name__)

# in-memory state
profile_status = "UNKNOWN"

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

def load_initial_status():
    global profile_status

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status 
        FROM  service_status
        WHERE service_name='profile'
    """)

    row = cursor.fetchone()

    if row:
        profile_status = row[0]
    else:
        profile_status = "DOWN"

    cursor.close()
    conn.close()

    print(f"Initial Status: {profile_status}")



def listen_for_updates():
    global profile_status

    pubsub= r.pubsub()

    pubsub.subscribe("circuit_updates")

    print("Subscribed to circuit_updates")

    for message in pubsub.listen():

        if message["type"] != "message":
            continue

        data = message["data"]

        print(f"Received : {data}")

        service, status = data.split(":")

        if service == "profile":
            profile_status = status
            print(f"profile_status = {profile_status}")



load_initial_status()

thread = threading.Thread(
    target=listen_for_updates,
    daemon=True
)

thread.start()

@app.route("/recommendations/<user_id>")
def recommendations(user_id):

    global profile_status  #

    print(f"profile_status ={profile_status}")
    if profile_status == "UP":
        # try:
        #     response = requests.get(
        #         f"http://localhost:5001/profile/{user_id}",
        #         timeout=2
        #     )
        # except:
        #     profile_status = "DOWN"

        # profile = response.json()

        # return jsonify({
        #     "source":"profile-service",
        #     "profile": profile, 
        #     "recommendations":[
        #         "Post 1",
        #         "Post 2"
        #     ]
        # })

        try:
            response = requests.get(
                f"http://localhost:5001/profile/{user_id}",
                timeout=2
            )
            profile_data = response.json()  #  Move this inside the try block

            return jsonify({
                "source": "profile-service",
                "profile": profile_data, 
                "recommendations": ["Post 1", "Post 2"]
            })
            
        except Exception as e:
            print(f"Profile service request failed: {e}")
            profile_status = "DOWN"

    else:

        return jsonify({
            "source":"fallback",
            "profile": None,
            "recommendations":[]
        }) 

app.run(
    host="0.0.0.0",
    port=5002,
    debug=True
)

