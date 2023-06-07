import requests
import os
import logging
from telegram import Bot
import time
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

VALID_KEYS = ['homeworks', 'current_date']


def check_tokens():
    """Проверка наличия токенов."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN]
    for token in tokens:
        if not token:
            logging.critical(f'Отсутствует обязательная'
                             f'переменная окружения: {token}'
                             f'Программа принудительно остановлена.'
                             )
            raise ValueError('no token')


def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    try:

        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('сообщение отправлено')
    except Exception as error:
        logging.error(f'оишбка при отправке сообщения {error}')


def get_api_answer(timestamp):
    """Получает ответ от апи Яндекс."""
    url = ENDPOINT
    headers = HEADERS
    params = {'from_date': timestamp}
    try:
        response = requests.get(url, headers=headers, params=params)
    except requests.RequestException:
        pass
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception


def check_response(response):
    """Проверяет полученный ответ."""
    if type(response) is not dict:
        raise TypeError
    if 'homeworks' not in response:
        raise Exception
    if type(response['homeworks']) is not list:
        raise TypeError
    if list(response.keys()) != VALID_KEYS:
        logging.error(f'Отсутствие ожидаемых ключей в ответе'
                      f'API{response.json().keys()} {VALID_KEYS}')
    return response


def parse_status(homework):
    """Проверка статуса домашней работы."""
    if 'homework_name' not in homework:
        raise Exception('Не получил ключ homework')
    if homework['status'] not in HOMEWORK_VERDICTS:
        logging.error('Неожиданный статус домашней работы,'
                      'обнаруженный в ответе API ')
        raise Exception()
    hw_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework["status"]]
    return (f'Изменился статус проверки работы "{hw_name}".{verdict}')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    print(timestamp)
    check_status = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response:
                homework = response['homeworks'][0]
                if homework['status'] != check_status:
                    message = parse_status(homework)
                    check_status = homework['status']
                    send_message(bot, message)

        except TypeError:
            logging.info('no hw')

        except IndexError:
            logging.info('no hw')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)

        time.sleep(600)


if __name__ == '__main__':
    main()
