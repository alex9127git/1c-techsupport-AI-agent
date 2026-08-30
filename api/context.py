from typing import Any


class Context:
    messages: list[dict[str, Any]]
    response_format: dict[str, Any]

    def __init__(self):
        self.messages = []

    def add_message(self, role, message):
        self.messages.append({
            'role': role,
            'content': message
        })

    def set_response_format(self, new_format):
        self.response_format = new_format


def get_empty_context() -> Context:
    """
    :return: Пустой контекст с системным промптом для агента Gigachat.
    """
    context = Context()
    context.add_message(
        'system',
        'Ты - ассистент в известной бизнес-корпорации, бухгалтерский отдел которой использует технологии 1С.\n'
        'Твоя задача - осуществлять техническую поддержку пользователей 1С и отвечать на вопросы, '
        'которые будут задавать пользователи. Если к сообщению приложено изображение, ты можешь его анализировать '
        'и использовать для получения дополнительной информации: ошибок, странностей в интерфейсе и прочего.\n'
        'Иногда пользователь может задать вопрос, где отсутствуют достаточное количество деталей для качественного '
        'ответа или вопрос сильно размытый. В таком случае тебе нужно уточнить вопрос у пользователя.\n'
        'Если вопрос не относится к 1С, тебе нужно объяснить пользователю, что ты отвечаешь только на вопросы, '
        'связанные с технической поддержкой 1С.йо'
    )
    context.set_response_format({
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'output': {
                    'type': 'string',
                    'description': 'Ответ ассистента'
                },
                'confidence_level': {
                    'type': 'integer',
                    'description': 'Уровень уверенности от 0 до 100'
                }
            },
            'required': ['output', 'confidence_level'],
            'strict': True
        }
    })
    return context

def get_confidence_context(messages_to_rate) -> Context:
    """
    :param messages_to_rate: Предыдущие сообщения, которые агент Gigachat будет оценивать.
    :return: Возвращает контекст, необходимый для оценки уровня уверенности отвечающего агента Gigachat.
    """
    context = Context()
    context.add_message(
        'system',
        'Ты - AI-агент в известной бизнес корпорации, бухгалтерский отдел которой использует технологии 1С.\n'
        'Их система использует AI-агента в отделе технической поддержки для того, чтобы помогать пользователям. '
        'Твоя задача - оценивать ответы AI-агента на предмет того, насколько они корректны и насколько хорошо отвечают'
        'на вопрос пользователя/уточняют неизвестные детали, и дать оценку в процентах от 0 до 100.\n'
        # '- 0–20: ответ неверен или опасен (может привести к потере данных);'
        # '- 21–50: частично верен, но упущены важные детали (релиз, последовательность);'
        # '- 51–80: верен, но не хватает ссылок на ИТС или уточнений;'
        # '- 81–100: исчерпывающий, безопасный, с учётом версии и возможных нюансов.'
    )
    context.set_response_format({
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'confidence_level': {
                    'type': 'integer',
                    'description': 'Уровень уверенности от 0 до 100'
                }
            },
            'required': ['confidence_level'],
            'strict': True
        }
    })
    for message in messages_to_rate:
        context.add_message(message['role'], message['content'])
    return context
