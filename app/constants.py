import os

BMR_CONSTANTS_MALE = os.environ.get('BMR_CONSTANTS_MALE', '66, 13.75 , 5, 6.8')
BMR_CONSTANTS_FEMALE = os.environ.get('BMR_CONSTANTS_FEMALE', '655, 9.56, 1.85, 4.68')
ACTIVITY_LEVEL = float(os.environ.get('ACTIVITY_LEVEL', 1.2))

def parse_tuple(env_var_value):
    values = env_var_value.split(',')
    return tuple(map(float, values))

BMR_CONSTANTS_MALE = parse_tuple(BMR_CONSTANTS_MALE)
BMR_CONSTANTS_FEMALE = parse_tuple(BMR_CONSTANTS_FEMALE)
