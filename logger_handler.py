import telegram

from logging import Handler, LogRecord


class TelegramBotHandler(Handler):
    def __init__(self, token: str, chat_id: str):
        super().__init__()
        self.token = token
        self.chat_id = chat_id

    def emit(self, record: LogRecord):
        logger_bot = telegram.Bot(token=self.token)
        logger_bot.send_message(
            self.chat_id,
            self.format(record)
        )
