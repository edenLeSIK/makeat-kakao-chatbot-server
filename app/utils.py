from flask import jsonify
from datetime import datetime, date
import random

BMR_CONSTANTS = {
    '남': (66, 13.75, 5, 6.8),
    '여': (655, 9.56, 1.85, 4.68)
}

ACTIVITY_LEVEL = 1.2

# 입력 값 유효성 검사 함수들
def is_valid_birth_date(birth_date):
    try:
        datetime.strptime(str(birth_date), "%y%m%d")
        return True
    except ValueError:
        return False

def is_valid_gender(gender):
    return gender.lower() in ('남', '여')

def is_valid_number(value):
    return str(value).isdigit()

def validate_input(params):
    errors = []

    birth_date = params['birth_date']['origin']
    gender = params['gender']['origin']
    height = params['height']['origin']
    weight = params['weight']['origin']
    goal_weight = params['goal_weight']['origin']

    if not is_valid_birth_date(birth_date):
        errors.append("🔺 생년월일을 정확하게 입력해주세요. (YYMMDD 형식)")
    if not is_valid_gender(gender):
        errors.append("🔺 성별은 '남' 또는 '여'로 정확히 입력해주세요.")
    if not is_valid_number(height) or len(str(height)) != 3:
        errors.append("🔺 신장을 정확하게 입력해주세요.")
    if not is_valid_number(weight):
        errors.append("🔺 몸무게는 숫자로만 정확하게 입력해주세요.")
    if not is_valid_number(goal_weight):
        errors.append("🔺 목표 체중은 숫자로만 정확하게 입력해주세요.")

    return errors

# BMR 및 칼로리 계산 함수들
def calculate_age(birth_date):
    today = date.today()
    birth_date = str(birth_date)  # Convert to string
    birth_date = datetime.strptime(birth_date, "%y%m%d").date()

    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def calculate_bmr_by_gender(age, gender, height, weight):
    bmr_constants = BMR_CONSTANTS[gender.lower()]
    bmr = bmr_constants[0] + (bmr_constants[1] * weight) + (bmr_constants[2] * height) - (bmr_constants[3] * age)
    return bmr

def calculate_daily_calories(bmr):
    return round(bmr * ACTIVITY_LEVEL)

# 메뉴 추천 관련 함수들
def get_menu_calories(menu_list):
    return sum(menu['calories'] for menu in menu_list)

def recommend_menu(menu_list, calorie_target, current_menu):
    available_menu_pool = [menu for menu in menu_list if menu not in current_menu]
    recommended_menu = random.choice([menu for menu in available_menu_pool if menu['calories'] <= calorie_target])
    return recommended_menu

# 응답 생성 함수들
def jsonify_success_response(text, quick_replies=None):
    response = {
        "version": "2.0",
        "template": {
             "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    }
    if quick_replies:
        response["template"]["quickReplies"] = quick_replies
    return jsonify(response)

def jsonify_error_response(errors):
    error_text = "\n".join(errors)
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": f"⛔️입력에 실패하였습니다. 정확한 정보를 다시 입력해주세요.\n\n{error_text}"
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "신체 정보를 다시 입력하고 싶어요.",
                    "action": "message",
                    "label": "신체 정보 수정"
                },
                {
                    "messageText": "종료할래요.",
                    "action": "message",
                    "label": "종료"
                },
            ]
        }
    }
    return jsonify(response)

def jsonify_missing_user_error():
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
    return jsonify(response)
