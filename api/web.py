import json
from os import environ
from requests import Request, Session
from api.auth import ApiToken
import uuid


def get_empty_session() -> Session:
    """
    Получает сессию, которая знает о сертификатах Сбербанка. Они не признаются автоматически,
    поэтому они хранятся в отдельном файле, который содержит цепочку сертификатов.
    Это позволяет сервису подключиться к сервису без необходимости изменять настройки системы,
    при этом оставляя защиту от атак MitM (Man-in-the-Middle).
    :return: Объект Session с особыми сертификатами, настроенными для принятия запросов из доверенных сайтов.
    """
    session = Session()
    session.verify = '../config/sberbank-ru-chain.pem'
    return session


def get_token_request() -> Request:
    """
    :return: Шаблон объекта Request с необходимыми данными для получения токена доступа к моделям Gigachat.
    """
    return Request(
        'POST',
        url='https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
        data={'scope': 'GIGACHAT_API_PERS'},
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {environ["AUTH_KEY"]}'
        }
    )


def get_model_query_request(token: ApiToken) -> Request:
    """
    :return: Шаблон объекта Request с необходимыми данными для получения токена доступа к моделям Gigachat.
    """
    return Request(
        'POST',
        url='https://api.giga.chat/v1/chat/completions',
        data=json.dumps({
            'model': 'Gigachat-2',
            'messages': [
                {
                    'role': 'user',
                    'content': 'Привет, Gigachat!'
                }
            ],
            'profanity_check': True
        }),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    )

