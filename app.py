from flask import Flask
import lamarun as lr
app = Flask(__name__)

@app.route("/")  # 기본 경로
def home():
    return "Hello, Flask!"

from flask import render_template

@app.route("/chat",methods=['GET','POST'])
def page():
    # run_ollama_api(model: str, prompt: str, stream: bool = True):
    lr.run_ollama_api(model = "gemma3:4b", prompt = method, stream = True)
    return render_template("index.html", title="홈페이지", message="Flask 시작!")



# @app.route("/result")
# def page():
#     return

if __name__ == "__main__":
    app.run(debug=True)