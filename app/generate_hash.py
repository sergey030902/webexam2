from werkzeug.security import generate_password_hash

def generate_hash(password):
    hashed_password = generate_password_hash(password)
    print(f'Хэш для пароля "{password}": {hashed_password}')

if __name__ == '__main__':
    password = input("Введите пароль для генерации хэша: ")
    generate_hash(password)
