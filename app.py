from flask import Flask, jsonify, request
from datetime import datetime
import sys
import sqlite3
import random

app = Flask(__name__)
DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, birth_date TEXT, gender TEXT, height INTEGER, weight INTEGER, goal_weight INTEGER, bmr REAL, created_date TEXT)')
    conn.commit()
    conn.close()

def calculate_bmr(age, gender, height, weight):
    if gender == '남':
        bmr = 66 + (13.75 * weight) + (5 * height) - (6.8 * age)
    else:
        bmr = 655 + (9.56 * weight) + (1.85 * height) - (4.68 * age)
    return bmr

def calculate_age(birth_date):
    today = datetime.now().date()
    birth_date = datetime.strptime(birth_date, "%y%m%d").date()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    return age

def insert_or_update_user(user_id, birth_date, gender, height, weight, goal_weight, bmr, created_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('INSERT INTO users (user_id, birth_date, gender, height, weight, goal_weight, bmr, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (user_id, birth_date, gender, height, weight, goal_weight, bmr, created_date))
    else:
        cursor.execute('UPDATE users SET birth_date = ?, gender = ?, height = ?, weight = ?, goal_weight = ?, bmr = ?, created_date = ? WHERE user_id = ?', (birth_date, gender, height, weight, goal_weight, bmr, created_date, user_id))
    conn.commit()
    conn.close()

@app.route("/user", methods=["POST"])
def calculate_bmr_for_user():
    create_users_table()
    
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    params = request_data['action']['detailParams']

    birth_date = str(params['birth_date']['origin'])
    gender = params['gender']['origin']
    height = int(params['height']['origin'])
    weight = int(params['weight']['origin'])
    goal_weight = int(params['goal_weight']['origin'])
    created_date = datetime.now().strftime("%Y-%m-%d")
    
    age = calculate_age(birth_date)
    bmr = calculate_bmr(age, gender, height, weight)

    insert_or_update_user(user_id, birth_date, gender, height, weight, goal_weight, bmr, created_date)
    
    activity_level = 1.2
    recommended_calories = round(bmr * activity_level)
    
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"🔔 입력해주신 정보를 기반으로 매일 새로운 <오늘의 식단🧑🏻‍🍳>을 추천해드릴게요!\n\n📏 키 {height}cm\n⚖️ 체중 {weight}kg\n🎯 목표 체중 {goal_weight}kg\n\n하루 권장 칼로리는 {recommended_calories}kcal입니다.\n(나이 {age}세, 성별 {gender}자 기준)"
                    }
                }
            ],
            "quickReplies": [
              {
                "messageText": "오늘의 식단을 추천해주세요!",
                "action": "message",
                "label": "오늘의 식단🧑🏻‍🍳"
              },
            ]
        }
    }

    return jsonify(response)

@app.route("/weight", methods=["POST"])
def update_weight():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    weight = int(request_data['action']['detailParams']['weight']['origin'])
    updated_date = datetime.now().strftime("%Y-%m-%d")

    create_users_table()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "신체 정보 설정을 먼저 진행해주세요."
                        }
                    }
                ],
                "quickReplies": [
                    {
                        "messageText": "신체 정보를 설정할래요!",
                        "action": "message",
                        "label": "신체 정보 설정"
                    },
                ]
            }
        }
    else:
        cursor.execute('UPDATE users SET weight = ?, created_date = ? WHERE user_id = ?', (weight, updated_date, user_id))
        conn.commit()

        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"⚖️ 체중이 {weight}kg로 업데이트 되었습니다."
                        }
                    }
                ]
            }
        }

    conn.close()
    return jsonify(response)


@app.route("/goal", methods=["POST"])
def update_goal_weight():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    goal_weight = int(request_data['action']['detailParams']['goal_weight']['origin'])
    updated_date = datetime.now().strftime("%Y-%m-%d")
    
    create_users_table()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "신체 정보 설정을 먼저 진행해주세요."
                        }
                    }
                ],
                "quickReplies": [
                    {
                        "messageText": "신체 정보를 설정할래요!",
                        "action": "message",
                        "label": "신체 정보 설정"
                    },
                ]
            }
        }
    else:
        cursor.execute('UPDATE users SET goal_weight = ?, created_date = ? WHERE user_id = ?', (goal_weight, updated_date, user_id))
        conn.commit()

        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": f"🎯 목표 체중이 {goal_weight}kg로 업데이트 되었습니다."
                        }
                    }
                ]
            }
        }

    conn.close()
    return jsonify(response)

@app.route("/menu", methods=["POST"])
def today_menu():
    user_id = request.get_json()['userRequest']['user']['id']
    
    create_users_table()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        response = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "신체 정보 설정을 먼저 진행해주세요."
                        }
                    }
                ],
                "quickReplies": [
                  {
                    "messageText": "신체 정보를 설정할래요!",
                    "action": "message",
                    "label": "신체 정보 설정"
                  },
                 {
                    "messageText": "종료",
                    "action": "message",
                    "label": "종료"
                  },
                ]
            }
        }
        conn.close()
        return jsonify(response)
    
    total_calories = int(user['bmr']) * 1.2  # 하루 권장 칼로리

    breakfast_calories = round(total_calories * 0.3)  # 아침 칼로리
    lunch_calories = round(total_calories * 0.4)  # 점심 칼로리
    dinner_calories = round(total_calories * 0.3)  # 저녁 칼로리

    meals = [
        '고기 새우 아보카도 덮밥', '와사비마요 목살 덮밥', '불고기 나물 비빔밥', '치즈 바질 파스타', '스테이크 샐러드', '아보카도 새우 콩피 샐러드', '마라 건두부 볶음', '그릭요거트 볼', '이뮨킥', '단백질부스트업'
    ]
    today_menu = random.choice(meals)

    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"🧑🏻‍🍳 오늘의 식단\n\n🍳 아침 {breakfast_calories}kcal\n﹡{today_menu}\n\n🌞 점심 {lunch_calories}kcal\n﹡{today_menu}\n\n🍽️ 저녁 {dinner_calories}kcal\n﹡{today_menu}"
                    }
                }
            ],
            "quickReplies": [
              {
                "messageText": "오늘의 식단 다시 추천해주세요!",
                "action": "message",
                "label": "다른 식단 추천받기"
              },
            ]
        }
    }

    conn.close()
    return jsonify(response)

@app.route("/", methods=["GET"])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    users_json = []
    for user in users:
        user_info = {
            "id": user['id'],
            "user_id": user['user_id'],
            "birth_date": user['birth_date'],
            "gender": user['gender'],
            "height": user['height'],
            "weight": user['weight'],
            "goal_weight": user['goal_weight'],
            "bmr": user['bmr'],
            "created_date": user['created_date']
        }
        users_json.append(user_info)

    conn.close()

    response = {
        "users": users_json
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(sys.argv[1]), debug=True)
