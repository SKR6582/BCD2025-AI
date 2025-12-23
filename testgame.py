import db_module.score as score
import db_module.db_connection as connection
import os
import sys
import random

def main():
    pass
random_equation = [f"{x}x{y}" for x in range(1,11) for y in range(1,11)]
gameover = False
equation_answer = [x*y for x in range(1,11) for y in range(1,11)]

q = random.choice(random_equation)
try :
    game = int(input(f"{q} = "))
except TypeError:
    print("Invalid input.\nInput must be an integer.")
    sys.exit()

if game == equation_answer[random_equation.index(q)]:
    print("Correct!")
    usrid = input("학번을 입력하세요 : ")
    user_data = score.get_ai_data(usrid)
    if user_data:
        c_score = int(user_data["score"]) + 5
    else:
        c_score = 5

    score.insert_ai_data(class_id=usrid, difficulty=0, client="1", score=c_score)

else :
    print("Incorrect!")

print(f"점수는 {score.get_ai_data(usrid)['score']}점 입니다.")