import logging
import os
import sys

from espeak_converter.config import config
from espeak_converter.ui.utils import ainput, choice
from espeak_converter.utils import request_utils

logger = logging.getLogger(__name__)


class UI:
    def __init__(self, converter):
        self.converter = converter

    async def start(self):
        while True:
            if not config.urls:
                await self.add_url()
                if not config.urls:
                    return
            answer = await choice(
                None, ["Добавить url.", "Начать выполнение.", "Настройки.", "Выход.,"]
            )
            if answer == 0:
                await self.add_url()
            elif answer == 1:
                await self.converter.run()
                logger.info("Преобразование выполнено")
                return
            elif answer == 2:
                await self.settings()
            elif answer == 3:
                return True

    async def add_url(self):
        url = await ainput("Введите url:")
        if not url:
            logger.info("Ничего не добавлено")
            return
        if self.converter.add_url(url):
            config.urls.append(url)
            config.save()

    async def settings(self):
        while True:
            options = []
            proxy = config.proxy or "не задан."
            options.append(f"Прокси: {proxy}")
            options.append(f"Число потоков: {config.max_jobs}.")
            options.append("Назад.")
            answer = await choice("Настройки", options)
            match answer:
                case 0:
                    await self.set_proxy()
                case 1:
                    await self.set_max_jobs()
                case 2:
                    config.save()
                    return

    async def set_proxy(self):
        config.proxy = await ainput("Введите прокси:") or None
        request_utils.set_proxy(config.proxy)
        if config.proxy is None:
            logger.info("Прокси сброшен")
        else:
            logger.info("Прокси установлен")

    async def set_max_jobs(self):
        total_cpu = os.cpu_count()
        prompt = (
            "Максимальное число потоков.\n"
            f"Минимум 2, максимально рекомендовано {total_cpu}.\n"
            "Число потоков должно быть чётным.\n"
            "Введите число потоков: "
        )
        while True:
            try:
                answer = int(await ainput(prompt))
            except ValueError:
                continue
            if answer < 2:
                print("2 - минимальное значение")
                continue
            if answer % 2:
                print("Число потоков должно быть чётным.")
                continue
            break
        if answer > total_cpu:
            factor = answer / total_cpu
            if factor <= 1.5:
                message = "Значение превышает рекомендованное"
            elif factor <= 3:
                message = "Значение превышает рекомендованное, запуск преобразования может значительно ухудшить производительность системы"
            elif factor <= 6:
                message = "Значение сильно превышает рекомендованное, запуск преобразования может значительно ухудшить производительность системы"
            else:
                message = "Значение очень сильно превышает рекомендованное! Запуск преобразования может вызвать нестабильность системы!"
            print(message)
        config.max_jobs = answer
