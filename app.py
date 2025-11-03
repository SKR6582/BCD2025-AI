from flask import Flask, render_template, jsonify
from db_module.score import get_ranking_by_difficulty

app = Flask(__name__)

@app.route("/")
def index():
    # 템플릿은 JS로 10초마다 /api/leaderboard를 호출하여 테이블을 갱신합니다.
    return render_template("index.html")

@app.get("/api/leaderboard")
def api_leaderboard():
    # 난이도: 1=쉬움, 2=노말, 3=하드
    try:
        easy = get_ranking_by_difficulty(1, limit=10)
        normal = get_ranking_by_difficulty(2, limit=10)
        hard = get_ranking_by_difficulty(3, limit=10)
        return jsonify({
            "easy": easy,
            "normal": normal,
            "hard": hard
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # 개발용 실행. 실제 서비스에서는 WSGI 서버 사용 권장
    app.run(debug=True)