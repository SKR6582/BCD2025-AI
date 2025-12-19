# Welcome to BCD2025 AI Project

## Setup

1. Clone this repository
2. Install dependencies
```shell
python.exe -m pip install -r requirements.txt
```
3. Set up the database
4. CD to project root
```shell
cp example.txt .env
```
**Caution** BCD2025-AI project requires dual.env. So You must set .env file both project root and /test_file dir.

5. Run
5-1. Run the web server
```shell
python.exe app.py
```
5-2. Run the game server
```shell
python.exe /test_file/ai_vs_human.py
```

---
> project requires python3.9~13