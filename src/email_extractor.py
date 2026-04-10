import re
from typing import List


class EmailExtractor:
    @staticmethod
    def extract_emails(text: str) -> List[str]:
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

    @staticmethod
    def validate_email(email: str) -> bool:
        """Проверяет, является ли строка валидным email адресом"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None