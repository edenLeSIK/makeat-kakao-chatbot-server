from flask import Flask, request, render_template, jsonify
from datetime import datetime
from app import app
from app.utils import (
    validate_input,
    calculate_age,
    calculate_bmr_by_gender,
    calculate_daily_calories,
    recommend_menu,
    jsonify_success_response,
    jsonify_error_response,
    jsonify_missing_user_error,
    jsonify_personal_information_agreement_error
)
from app.models import (
    get_db_connection,
    create_users_table,
    insert_or_update_user,
    get_user,
    create_weight_history_table,
    create_goal_weight_history_table,
    insert_weight_history,
    insert_goal_weight_history,
    get_weight_history,
    get_goal_weight_history,
    get_date_in_yymmdd_format
)
import requests
import json

REST_API_KEY = "29682897e0e51ea9e0dc7c80d76ab18a"

@app.route("/user", methods=['POST'])
def insert_user_profile():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    params = request_data['action']['detailParams']

    otp = params["profile"]["origin"]
    otp_url = f"{otp}?rest_api_key={REST_API_KEY}"

    otp_response = requests.get(otp_url)
    profile_data = otp_response.json()

    name = profile_data.get("nickname", "")
    gender = profile_data.get("gender", "")
    birthyear = profile_data.get("birthyear", "")
    birthday = profile_data.get("birthday", "")

    create_users_table()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.execute('INSERT INTO users (user_id, name, birthdate, gender) VALUES (?, ?, ?, ?)', (user_id, name, f"{birthyear}{birthday}", gender))

    response_text = f"👋🏻 반가워요. {name}님!\n아래의 버튼을 눌러 신체 정보 설정을 이어서 진행해주세요."
    quick_replies = [
        {
            "action": "block",
            "label": "신체 정보 설정",
            "blockId": "64abab0d0069f54fc7a3429b",
            "extra": {
                "": ""
            }
        }
    ]

    return jsonify_success_response(response_text, quick_replies)

@app.route("/physical_info", methods=["POST"])
def calculate_bmr_for_user():
    create_users_table()

    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    params = request_data['action']['detailParams']

    errors = validate_input(params)
    if errors:
        return jsonify_error_response(errors)

    user = get_user(user_id)
    if user:
        birthdate = user['birthdate']
        gender = user['gender']
        if gender == "female":
            gender_display = "여"
        elif gender == "male":
            gender_display = "남"
    else:
        return jsonify_personal_information_agreement_error()

    height = float(params['height']['origin'])
    weight = float(params['weight']['origin'])
    goal_weight = float(params['goal_weight']['origin'])

    created_date = datetime.now().strftime("%Y-%m-%d")
    age = calculate_age(birthdate)
    bmr = calculate_bmr_by_gender(age, gender, height, weight)

    insert_or_update_user(user_id, birthdate, gender, height, weight, goal_weight, bmr, created_date)

    recommended_calories = calculate_daily_calories(bmr)

    response = jsonify_success_response(
        f"🔔 입력해주신 정보를 기반으로 매일 새로운 <오늘의 식단🧑🏻‍🍳>을 추천해드릴게요!\n\n📏 키 {height}cm\n⚖️ 체중 {weight}kg\n🎯 목표 체중 {goal_weight}kg\n\n하루 권장 칼로리는 {recommended_calories}kcal입니다.\n(나이 {age}세, 성별 {gender_display}자 기준)",
        [
            {
                "messageText": "🧑🏻‍🍳 오늘의 식단을 추천해주세요!",
                "action": "message",
                "label": "오늘의 식단🧑🏻‍🍳"
            },
            {
                "messageText": "신체 정보를 수정하고 싶어요.",
                "action": "message",
                "label": "신체 정보 수정🧍🏻‍♀️"
            },
            {
                "messageText": "성별을 수정하고 싶어요.",
                "action": "message",
                "label": "성별 수정🚻"
            },
            {
                "messageText": "나이를 수정하고 싶어요.",
                "action": "message",
                "label": "생년월일 수정🗓️"
            }
        ]
    )
    
    return response

@app.route("/gender", methods=["POST"])
def update_gender():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']

    gender = request_data.get("action", {}).get("params", {}).get("gender")
    print(1, gender)

    if gender in ["여", "여자"]:
        gender = "female"
    elif gender in ["남", "남자"]:
        gender = "male"

    if not gender:
        return jsonify_error_response(["성별을 입력하세요."])

    user = get_user(user_id)
    if not user:
        return jsonify_personal_information_agreement_error()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET gender = ? WHERE user_id = ?', (gender, user_id))

    print(2, gender)

    return jsonify_success_response(f"성별이 {gender}로 업데이트 되었습니다.")

@app.route("/birthdate", methods=["POST"])
def update_birthdate():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']

    birthdate_str = request_data.get("action", {}).get("params", {}).get("birthdate")
    
    if not birthdate_str:
        return jsonify_error_response(["생년월일을 다시 입력하세요."])

    try:
        birthdate_data = json.loads(birthdate_str)
    except json.JSONDecodeError:
        return jsonify_error_response(["잘못된 JSON 형식입니다."])

    birthdate = birthdate_data.get("value")
    
    if not birthdate:
        return jsonify_error_response(["생년월일을 입력하세요."])

    birthdate = birthdate.replace("-", "")

    user = get_user(user_id)
    if not user:
        return jsonify_personal_information_agreement_error()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET birthdate = ? WHERE user_id = ?', (birthdate, user_id))

    return jsonify_success_response(f"생년월일이 {birthdate}로 업데이트 되었습니다.")

@app.route("/info", methods=["POST"])
def get_user_info():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']

    create_users_table()
    create_weight_history_table()
    create_goal_weight_history_table()

    user = get_user(user_id)

    if not user or not user['height'] or not user['weight'] or not user['goal_weight'] or not user['bmr']:
        return jsonify_missing_user_error()
    else:
        name = user['name']
        birthdate = user['birthdate']
        height = user['height']
        weight = user['weight']
        goal_weight = user['goal_weight']
        bmr = user['bmr']
        gender = user["gender"]
        if gender == "female":
            gender_display = "여"
        elif gender == "male":
            gender_display = "남"

        age = calculate_age(birthdate)
        recommended_calories = calculate_daily_calories(bmr)

    response = jsonify_success_response(
        f"{name}님의 정보를 알려드릴게요😃\n\n📏 키 {height}cm\n⚖️ 체중 {weight}kg\n🎯 목표 체중 {goal_weight}kg\n\n하루 권장 칼로리는 {recommended_calories}kcal입니다.\n(나이 {age}세, 성별 {gender_display}자 기준)"
    )

    return response

@app.route("/weight", methods=["POST"])
def update_weight():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    weight = float(request_data['action']['detailParams']['weight']['origin'])
    updated_date = datetime.now().strftime("%Y-%m-%d")

    create_users_table()
    create_weight_history_table()

    user = get_user(user_id)

    if not user:
        return jsonify_missing_user_error()

    previous_weight = user['weight']
    weight_difference = weight - previous_weight

    weight_difference_str = f"{weight_difference:.2f}"

    if weight_difference > 0:
        weight_change_message = f"+{weight_difference_str}kg 증가했"
    elif weight_difference < 0:
        weight_change_message = f"{weight_difference_str}kg 감소했"
    else:
        weight_change_message = "변동없"

    insert_weight_history(user_id, weight, updated_date)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET weight = ?, created_date = ? WHERE user_id = ?', (weight, updated_date, user_id))

    goal_weight = user['goal_weight']
    remaining_weight_to_goal = goal_weight - weight
    
    remaining_weight_to_goal_str = f"{remaining_weight_to_goal:.2f}"

    response = jsonify_success_response(
        f"⚖️ 체중이 {previous_weight}kg에서 {weight}kg로 {weight_change_message}어요!\n\n⚽️ 목표까지 {remaining_weight_to_goal_str}kg 남았어요. 목표 달성까지 화이탱!",
        [
            {
                "messageText": "목표를 수정할래요!",
                "action": "message",
                "label": "목표 체중 수정"
            },
            {
                "messageText": "지금까지의 체중 변화를 보고싶어요!",
                "action": "message",
                "label": "체중 변화 살펴보기"
            }
        ]
    )

    return response

@app.route('/weight_history', methods=["POST"])
def weight_history():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']

    create_weight_history_table()
    create_users_table()

    user = get_user(user_id)

    if not user:
        return jsonify_missing_user_error()

    weight_history = get_weight_history(user_id)
    if not weight_history:
        return jsonify_success_response("체중 변경 이력이 없어요.")

    weight_history.sort(key=lambda x: x['date'])

    weight_history.reverse()

    weight_history_text = "\n".join([f"{get_date_in_yymmdd_format(history['date'])} {history['weight']}kg" for history in weight_history])

    response = jsonify_success_response(f"⚖️ 체중 변경 히스토리 \n\n{weight_history_text}")

    return response

@app.route("/goal", methods=["POST"])
def update_goal_weight():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    goal_weight = float(request_data['action']['detailParams']['goal_weight']['origin'])
    updated_date = datetime.now().strftime("%Y-%m-%d")

    create_users_table()
    create_goal_weight_history_table()

    user = get_user(user_id)

    if not user:
        return jsonify_missing_user_error()
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET goal_weight = ?, created_date = ? WHERE user_id = ?', (goal_weight, updated_date, user_id))
        conn.commit()
        conn.close()

        insert_goal_weight_history(user_id, goal_weight, updated_date)

    response = jsonify_success_response(
        f"🎯 목표 체중이 {goal_weight}kg로 업데이트 되었습니다.",
        [
            {
                "messageText": "지금까지 세웠던 목표를 살펴볼래요!",
                "action": "message",
                "label": "목표 변화 살펴보기"
            }
        ]
    )

    return response

@app.route('/goal_history', methods=["POST"])
def goal_weight_history():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']

    create_goal_weight_history_table()

    user = get_user(user_id)

    if not user:
        return jsonify_missing_user_error()

    goal_weight_history = get_goal_weight_history(user_id)
    
    if not goal_weight_history:
        return jsonify_success_response("목표 체중 변경 이력이 없어요.")

    goal_weight_history.sort(key=lambda x: x['date'])

    goal_weight_history.reverse()

    goal_weight_history_text = "\n".join([f"{get_date_in_yymmdd_format(history['date'])} {history['goal_weight']}kg" for history in goal_weight_history])

    response = jsonify_success_response(f"🎯 목표 체중 변경 히스토리 \n\n{goal_weight_history_text}")

    return response

@app.route("/menu", methods=["POST"])
def today_menu():
    user_id = request.get_json()['userRequest']['user']['id']

    create_users_table()

    user = get_user(user_id)

    if not user:
        return jsonify_missing_user_error()

    current_weight = user['weight']
    goal_weight = user['goal_weight']
    bmr = user['bmr']

    if goal_weight > current_weight:
        total_calories = calculate_daily_calories(bmr) + 500
    elif goal_weight < current_weight:
        total_calories = calculate_daily_calories(bmr) - 500
    else:
        total_calories = calculate_daily_calories(bmr)

    # 아침, 점심, 저녁 식단의 칼로리를 설정
    breakfast_calories = round(total_calories * 0.3)
    lunch_calories = round(total_calories * 0.4)
    dinner_calories = round(total_calories * 0.3)

    # menus.json 파일을 읽어와 메뉴 데이터를 가져옴
    with open('data/menus.json', 'r') as json_file:
        menu_list = json.load(json_file)

    breakfast = []
    lunch = []
    dinner = []

    # 아침 메뉴 추천
    breakfast_menu = recommend_menu(menu_list, breakfast_calories, 'breakfast')
    breakfast.append(breakfast_menu)
    menu_list.remove(breakfast_menu)  # 이미 선택한 아침 메뉴는 리스트에서 제거

    # 점심 메뉴 추천
    lunch_menu = recommend_menu(menu_list, lunch_calories, 'lunch')
    lunch.append(lunch_menu)
    menu_list.remove(lunch_menu)  # 이미 선택한 점심 메뉴는 리스트에서 제거

    # 저녁 메뉴 추천
    dinner_menu = recommend_menu(menu_list, dinner_calories, 'dinner')
    dinner.append(dinner_menu)

    text = "🧑🏻‍🍳 오늘의 식단\n\n"
    text += f"고객님의 현재 체중은 {current_weight}kg, 목표 체중은 {goal_weight}kg이에요!\n"
    text += f"목표를 달성하기 위해 제안해드리는 하루 권장 칼로리는 {total_calories}kcal랍니다.\n\n"
    text += f"🍳 아침 {breakfast_calories}kcal\n﹡{breakfast[0]['menu']}\n\n"
    text += f"🌞 점심 {lunch_calories}kcal\n﹡{lunch[0]['menu']}\n\n"
    text += f"🍽️ 저녁 {dinner_calories}kcal\n﹡{dinner[0]['menu']}"

    response = jsonify_success_response(text, [
        {
            "messageText": "🧑🏻‍🍳 오늘의 식단 다시 추천해주세요!",
            "action": "message",
            "label": "다른 식단 추천받기"
        }
    ])

    return response

@app.route("/", methods=["GET"])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()

    return render_template('index.html', users=users)
