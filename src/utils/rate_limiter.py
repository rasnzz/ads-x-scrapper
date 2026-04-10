import time
from typing import Optional
from datetime import datetime, timedelta


class RateLimiter:
    def __init__(self, max_requests: int = 2, time_window: int = 1):
        """
        Ограничитель частоты запросов
        
        Args:
            max_requests: максимальное количество запросов за временной интервал
            time_window: временной интервал в секундах
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def wait_if_needed(self):
        """Ждет, если необходимо, чтобы соблюсти ограничение частоты"""
        now = datetime.now()
        
        # Удаляем старые запросы из временного окна
        self.requests = [req_time for req_time in self.requests if now - req_time < timedelta(seconds=self.time_window)]
        
        # Если достигнуто максимальное количество запросов, ждем
        if len(self.requests) >= self.max_requests:
            sleep_time = (self.requests[0] + timedelta(seconds=self.time_window)) - now
            if sleep_time.total_seconds() > 0:
                time.sleep(sleep_time.total_seconds())
                # После сна снова удаляем старые запросы
                now = datetime.now()
                self.requests = [req_time for req_time in self.requests if now - req_time < timedelta(seconds=self.time_window)]
        
        # Добавляем текущий запрос
        self.requests.append(now)