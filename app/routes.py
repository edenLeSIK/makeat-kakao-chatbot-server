from flask import Flask, request, render_template
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
from app import menus

ACTIVITY_LEVEL = 1.2

@app.route("/user", methods=["POST"])
def calculate_bmr_for_user():
    create_users_table()

    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    params = request_data['action']['detailParams']

    errors = validate_input(params)
    if errors:
        return jsonify_error_response(errors)

    birth_date = params['birth_date']['origin']
    gender = params['gender']['origin']
    height = int(params['height']['origin'])
    weight = int(params['weight']['origin'])
    goal_weight = int(params['goal_weight']['origin'])

    created_date = datetime.now().strftime("%Y-%m-%d")
    age = calculate_age(birth_date)
    bmr = calculate_bmr_by_gender(age, gender, height, weight)

    insert_or_update_user(user_id, birth_date, gender, height, weight, goal_weight, bmr, created_date)

    recommended_calories = calculate_daily_calories(bmr, ACTIVITY_LEVEL)

    response = jsonify_success_response(
        f"🔔 입력해주신 정보를 기반으로 매일 새로운 <오늘의 식단🧑🏻‍🍳>을 추천해드릴게요!\n\n📏 키 {height}cm\n⚖️ 체중 {weight}kg\n🎯 목표 체중 {goal_weight}kg\n\n하루 권장 칼로리는 {recommended_calories}kcal입니다.\n(나이 {age}세, 성별 {gender}자 기준) \n\n(입력을 잘못했을 경우 아래의 신체 정보 수정 버튼을 눌러 다시 입력해주시길 바랍니다.)",
        [
            {
                "messageText": "신체 정보를 수정하고 싶어요.",
                "action": "message",
                "label": "신체 정보 수정"
            },
            {
                "messageText": "오늘의 식단을 추천해주세요!",
                "action": "message",
                "label": "오늘의 식단🧑🏻‍🍳"
            }
        ]
    )
    
    return response

@app.route("/info", methods=["POST"])
def get_user_info():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']

    create_users_table()
    create_weight_history_table()
    create_goal_weight_history_table()

    user = get_user(user_id)

    if not user:
        return jsonify_missing_user_error()
    else:
        height = user['height']
        weight = user['weight']
        goal_weight = user['goal_weight']
        bmr = user['bmr']

        recommended_calories = calculate_daily_calories(bmr)

    response = jsonify_success_response(
        f"고객님의 정보를 알려드릴게요😃\n\n📏 키 {height}cm\n⚖️ 체중 {weight}kg\n🎯 목표 체중 {goal_weight}kg\n\n하루 권장 칼로리는 {recommended_calories}kcal입니다."
    )

    return response

@app.route("/weight", methods=["POST"])
def update_weight():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    weight = int(request_data['action']['detailParams']['weight']['origin'])
    updated_date = datetime.now().strftime("%Y-%m-%d")

    create_users_table()
    create_weight_history_table()

    user = get_user(user_id)

    if not user:
        return jsonify_missing_user_error()
    
    previous_weight = user['weight']
    weight_difference = weight - previous_weight

    if weight_difference > 0:
        weight_change_message = f"+{weight_difference}kg 증가했"
    elif weight_difference < 0:
        weight_change_message = f"-{abs(weight_difference)}kg 감소했"
    else:
        weight_change_message = "변동없"

    insert_weight_history(user_id, weight, updated_date)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET weight = ?, created_date = ? WHERE user_id = ?', (weight, updated_date, user_id))

    goal_weight = user['goal_weight']
    remaining_weight_to_goal = goal_weight - weight

    response = jsonify_success_response(
        f"⚖️ 체중이 {previous_weight}kg에서 {weight}kg로 수정됐어요.\n{weight_change_message}어요!\n\n⚽️ 목표까지 {remaining_weight_to_goal}kg 남았어요. 화이탱~",
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

    weight_history_text = "\n".join([f"{get_date_in_yymmdd_format(history['date'])} {history['weight']}kg" for history in weight_history])

    response = jsonify_success_response(f"⚖️ 체중 변경 히스토리 \n\n{weight_history_text}")

    return response

@app.route("/goal", methods=["POST"])
def update_goal_weight():
    request_data = request.get_json()
    user_id = request_data['userRequest']['user']['id']
    goal_weight = int(request_data['action']['detailParams']['goal_weight']['origin'])
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

    breakfast_calories = round(total_calories * 0.3)  # 아침 칼로리
    lunch_calories = round(total_calories * 0.4)  # 점심 칼로리
    dinner_calories = round(total_calories * 0.3)  # 저녁 칼로리

    menu_list = menus.menus()

    breakfast = []
    lunch = []
    dinner = []

    # 아침 메뉴 추천
    breakfast.append(recommend_menu(menu_list, breakfast_calories, []))
    # 점심 메뉴 추천
    lunch.append(recommend_menu(menu_list, lunch_calories, breakfast))
    # 저녁 메뉴 추천
    dinner.append(recommend_menu(menu_list, dinner_calories, breakfast + lunch))

    text = "🧑🏻‍🍳 오늘의 식단\n\n"
    text += f"고객님의 현재 체중은 {current_weight}kg, 목표 체중은 {goal_weight}kg이에요!"
    text += f"목표를 달성하기 위해 제안해드리는 하루 권장 칼로리는 {total_calories}kcal이랍니다.\n"
    text += f"🍳 아침 {breakfast_calories}kcal\n﹡{breakfast[0]['name']}\n\n"
    text += f"🌞 점심 {lunch_calories}kcal\n﹡{lunch[0]['name']}\n\n"
    text += f"🍽️ 저녁 {dinner_calories}kcal\n﹡{dinner[0]['name']}"

    response = jsonify_success_response(text, [
        {
            "messageText": "오늘의 식단 다시 추천해주세요!",
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
