from flask import Flask, render_template, jsonify, request
from db_module.score import get_ranking_by_difficulty
from db_module.quiz import add_quiz, list_quiz_titles, update_quiz, delete_quiz

app = Flask(__name__, static_folder='templates', static_url_path='/templates')

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

@app.route("/quiz")
def quiz_manager():
    return render_template("quiz.html")

@app.get("/api/quizzes")
def api_list_quizzes():
    try:
        category = request.args.get("category")
        difficulty = request.args.get("difficulty", type=int)
        quizzes = list_quiz_titles(category=category, difficulty=difficulty, include_correct=True)
        return jsonify(quizzes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/quizzes")
def api_add_quiz():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        quiz_id = add_quiz(
            difficulty=data.get("difficulty"),
            title=data.get("title"),
            description=data.get("description"),
            category=data.get("category"),
            correct=data.get("correct")
        )
        return jsonify({"id": quiz_id, "message": "Quiz added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.put("/api/quizzes/<int:quiz_id>")
def api_update_quiz(quiz_id):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        success = update_quiz(
            quiz_id=quiz_id,
            difficulty=data.get("difficulty"),
            title=data.get("title"),
            description=data.get("description"),
            category=data.get("category"),
            correct=data.get("correct")
        )
        if success:
            return jsonify({"message": "Quiz updated successfully"})
        else:
            return jsonify({"error": "Quiz not found or no changes made"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.delete("/api/quizzes/<int:quiz_id>")
def api_delete_quiz(quiz_id):
    try:
        success = delete_quiz(quiz_id)
        if success:
            return jsonify({"message": "Quiz deleted successfully"})
        else:
            return jsonify({"error": "Quiz not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # 개발용 실행. 실제 서비스에서는 WSGI 서버 사용 권장
    app.run(debug=True, host='0.0.0.0', port=55000)