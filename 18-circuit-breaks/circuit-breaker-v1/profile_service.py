from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/profile/<user_id>")
def get_profile(user_id):
    print("PROFILE SERVICE CALLED")
    return jsonify({
        "userId": user_id,
        "name": "Lalith Sharma",
        "city": "chennai"
    })

@app.route("/health")
def health():
    return jsonify({
        "status", "UP"
    })


app.run(
    host="0.0.0.0",
    port=5001,
    debug=True
)














