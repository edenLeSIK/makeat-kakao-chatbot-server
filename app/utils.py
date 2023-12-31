from flask import jsonify
from datetime import datetime, date
import random
from app.constants import BMR_CONSTANTS_MALE, BMR_CONSTANTS_FEMALE, ACTIVITY_LEVEL

# 입력 값 유효성 검사 함수들
def is_valid_birthdate(birthdate):
    try:
        datetime.strptime(str(birthdate), "%y%m%d")
        return True
    except ValueError:
        return False

def is_valid_gender(gender):
    return gender.lower() in ('남', '여')

def is_valid_number(value):
    try:
        float_value = float(value)
        return True
    except ValueError:
        return False

def validate_input(params):
    errors = []

    height = params['height']['origin']
    weight = params['weight']['origin']
    goal_weight = params['goal_weight']['origin']

    # 키가 숫자로 변환 가능하고 100 이상인지 확인
    if not is_valid_number(height):
        errors.append("🔺 올바른 숫자 형식의 키를 입력해주세요.")
    elif float(height) < 100:
        errors.append("🔺 키를 정확히 입력해주세요.")

    # 몸무게와 목표 체중이 숫자로 변환 가능한지 확인
    if not is_valid_number(weight):
        errors.append("🔺 올바른 숫자 형식의 몸무게를 입력해주세요.")
    if not is_valid_number(goal_weight):
        errors.append("🔺 올바른 숫자 형식의 목표 체중을 입력해주세요.")

    return errors

# BMR 및 칼로리 계산 함수들
def calculate_age(birthdate):
    today = datetime.now().date()
    
    try:
        birthdate = datetime.strptime(birthdate, "%Y%m%d").date()
    except ValueError:
        return None

    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def calculate_bmr_by_gender(age, gender, height, weight):
    # gender = gender.lower()  # 입력된 성별 값을 소문자로 변환
    if gender == 'male':
        bmr_constants = BMR_CONSTANTS_MALE
    elif gender == 'female':
        bmr_constants = BMR_CONSTANTS_FEMALE
    else:
        raise ValueError("성별 입력 실패")

    bmr = bmr_constants[0] + (bmr_constants[1] * weight) + (bmr_constants[2] * height) - (bmr_constants[3] * age)
    return bmr

def calculate_daily_calories(bmr):
    return round(bmr * ACTIVITY_LEVEL)

# 메뉴 추천 관련 함수들
def get_menu_calories(menu_list):
    return sum(menu['calories'] for menu in menu_list)

def recommend_menu(menu_list, calories_target, meal_type):
    valid_menu = []

    for menu in menu_list:
        calorie_difference = abs(menu['total_calories'] - calories_target)
        if calorie_difference <= 10:
            valid_menu.append(menu)

    if meal_type == 'breakfast':
        valid_menu = [menu for menu in valid_menu if menu['breakfast'] == 1]

    if valid_menu:
        recommended_menu = random.choice(valid_menu)
        
        if recommended_menu.get('rice') == 1:
            recommended_menu['menu'] += " & 밥"
        
        return recommended_menu
    else:
        return "추천 메뉴 없음"

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
                    "messageText": "성별을 수정하고 싶어요.",
                    "action": "message",
                    "label": "성별 수정"
                },
                {
                    "messageText": "생년월일을 수정하고 싶어요",
                    "action": "message",
                    "label": "생년월일 수정"
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

def jsonify_personal_information_agreement_error():
    response = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "개인 정보 이용에 동의하셔야 메이킷 서비스를 이용할 수 있어요!"
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "개인 정보 이용 동의",
                    "action": "message",
                    "label": "개인 정보 이용 동의"
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