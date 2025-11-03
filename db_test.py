import db_module.db_connection as db_connection
import db_module.score as score
import random

for x in range(10):
    score.insert_ai_data(classid=random.randint(10101,11235),difficulty=3,score=random.randint(100,500),client="No.1")





# import lamarun
# print(score.get_ai_data("10613"))