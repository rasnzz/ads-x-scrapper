from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List
import re


class WebsiteParser:
    def __init__(self, driver: WebDriver, timeout: int = 30):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def extract_emails_from_page(self) -> List[str]:
        """Извлекает email адреса со страницы внешнего сайта"""
        try:
            # Ждем загрузки содержимого страницы
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            # Если страница не загрузилась вовремя, продолжаем с тем, что есть
            pass
        
        # Получаем текст страницы
        page_text = self.driver.find_element(By.TAG_NAME, "body").text
        
        # Находим email адреса в тексте
        emails = self._extract_emails(page_text)
        
        return emails

    def _extract_emails(self, text: str) -> List[str]:
        """Извлекает email адреса из текста"""
        if not text:
            return []
        
        # Регулярное выражение для поиска email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Фильтруем найденные совпадения, чтобы исключить некорректные адреса
        valid_emails = []
        for email in emails:
            # Простая проверка на валидность email
            if email.count('@') == 1 and '.' in email.split('@')[1]:
                if email not in valid_emails:  # Избегаем дубликатов
                    valid_emails.append(email)
        
        return valid_emails