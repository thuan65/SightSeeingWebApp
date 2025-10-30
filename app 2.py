from flask import Flask, json, request, jsonify, Response
from sqlalchemy import create_engine, text

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False


# Kết nối tới database SQLite
engine = create_engine("sqlite:///places.db")

@app.route("/search_filter", methods=["GET"])
def search_filter():
    city = request.args.get("city", "")
    tag = request.args.get("tag", "")
    min_rating = float(request.args.get("rating", 0))

    query = "SELECT * FROM places WHERE 1=1"
    params = {}

    if city:
        query += " AND city LIKE :city"
        params["city"] = f"%{city}%"

    if tag:
        query += " AND tags LIKE :tag"
        params["tag"] = f"%{tag}%"

    query += " AND rating >= :min_rating"
    params["min_rating"] = min_rating

    with engine.connect() as conn:
        results = conn.execute(text(query), params).mappings().all()

    response = json.dumps([dict(row) for row in results], ensure_ascii=False)

    return Response(response, content_type="application/json; charset=utf-8")

if __name__ == "__main__":
    app.run(debug=True)
