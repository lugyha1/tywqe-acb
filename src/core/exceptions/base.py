class AppError(Exception):
    user_message = "⚠️ Что-то пошло не так. Попробуйте ещё раз."


class ValidationAppError(AppError):
    user_message = "🔎 Не удалось распознать запрос. Проверьте данные."


class RateLimitExceededError(AppError):
    user_message = "⏳ Слишком много действий. Пожалуйста, немного подождите."
