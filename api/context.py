from typing import Any


class Context:
    messages: list[dict[str, Any]]
    response_format: dict[str, Any]

    def __init__(self):
        self.messages = []

    def add_message(self, role, message, attachments=None):
        message = {
            'role': role,
            'content': message
        }
        if attachments is not None:
            message['attachments'] = attachments
        self.messages.append(message)

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
        'Тебе может быть передан файл .txt, содержащий дополнительный контекст для решения проблемы. '
        'Опирайся в первую очередь на него. Если там не содержится ответа или если файл отсутствует, '
        'можешь опираться на данные из Интернета для ответа на запрос пользователя.\n'
        'Иногда пользователь может задать вопрос, где отсутствуют достаточное количество деталей для качественного '
        'ответа или вопрос сильно размытый. В таком случае тебе нужно уточнить запрос у пользователя. '
        'Особенно важно уточнять запрос в случае, если твой ответ будет сильно зависеть от этого уточнения.'
        '(например, если функциональность, которую ты предложишь, будет доступна только для определёной версии '
        'программы).\n'
        'Задавай только те вопросы, которые помогут тебе уточнить запрос пользователя. Добавляй в своё сообщение '
        'только то, что относится к ответу или уточнению.\n'
        'Избегай пустых вопросов в конце: они не дают никакой дополнительной информации.\n'
        'Если вопрос не относится к 1С, тебе нужно объяснить пользователю, что ты отвечаешь только на вопросы, '
        'связанные с технической поддержкой 1С.'
    )
    context.set_response_format({
        'type': 'text',
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

def get_rewording_context(messages_to_rate) -> Context:
    """
    :param messages_to_rate: Предыдущие сообщения, которые агент Gigachat будет переформулировать.
    :return: Возвращает контекст, необходимый для переформулирования контекста для агента Gigachat.
    """
    context = Context()
    context.add_message(
        'system',
        'Ты - AI-агент в известной бизнес корпорации, бухгалтерский отдел которой использует технологии 1С.\n'
        'Их система использует AI-агента в отделе технической поддержки для того, чтобы помогать пользователям. '
        'Твоя задача - переформулировать контекст переданного тебе диалога, и вычленить оттуда самодостаточный вопрос '
        'пользователя, в котором будет содержаться весь необходимый контекст.'
    )
    context.set_response_format({
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Полученный запрос в форме вопроса'
                }
            },
            'required': ['query'],
            'strict': True
        }
    })
    for message in messages_to_rate:
        context.add_message(message['role'], message['content'])
    return context


def get_answer_with_confidence_context(messages_to_answer, attachments=None) -> Context:
    """
    Возвращает контекст для ответа агента с одновременной оценкой уверенности:
    один запрос с json_schema {'answer', 'confidence_level'} вместо двух отдельных.
    Нужен, чтобы уложиться в тайминг ТЗ (< 5 секунд).
    """
    context = get_empty_context()
    context.set_response_format({
        'type': 'json_schema',
        'schema': {
            'type': 'object',
            'properties': {
                'answer': {
                    'type': 'string',
                    'description': 'Ответ агента технической поддержки'
                },
                'confidence_level': {
                    'type': 'integer',
                    'description': 'Уровень уверенности в корректности ответа от 0 до 100'
                }
            },
            'required': ['answer', 'confidence_level'],
            'strict': True
        }
    })
    for message in messages_to_answer:
        context.add_message(message['role'], message['content'])
    if attachments is not None:
        context.messages[-1]['attachments'] = attachments
    return context


def get_image_analysis_context() -> Context:
    """
    Возвращает контекст для анализа скриншота интерфейса 1С.
    Ответ — свободный текст (без json_schema): модель описывает, что видит
    на изображении, и формулирует рекомендацию по устранению ошибки.
    """
    context = get_empty_context()
    context.set_response_format({'type': 'text'})
    return context