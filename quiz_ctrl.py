from db_module import quiz
import subprocess
from random import randint


def log(fn):
    def wrapper(*args, **kwargs):
        print(f"[{fn.__name__}]")
        return fn(*args, **kwargs)
    return wrapper


def safe_input(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
            return None
    return wrapper

quizs = [data for data in quiz.list_quiz_titles()]


class Randomizer:
    def __init__(self):
        self.quiz = quizs[randint(0, len(quizs) - 1)]

    def get_quiz(self):
        return self.quiz

    def show_quiz(self):
        for q in quizs:
            print(q)

    def test(self):
        print("debug")
        print(self.quiz)

@safe_input
def get_menu_input():
    return int(input("Active works. 1, 2, 3 > "))

while True:
    print("Test page.")
    opt = get_menu_input()

    if opt == 1:
        print(Randomizer().get_quiz())

    elif opt == 2:
        Randomizer().show_quiz()

    elif opt == 3:
        break


