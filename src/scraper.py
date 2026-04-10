import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Dict, List
import re


def connect_to_profile(selenium_endpoint: str) -> webdriver.Chrome:
    """
    selenium_endpoint – строка вида "127.0.0.1:PORT", полученная из ответа start_profile
    """
    options = Options()
    options.add_experimental_option("debuggerAddress", selenium_endpoint)
    driver = webdriver.Chrome(options=options)
    return driver


class TwitterEmailScraper:
    def __init__(self, driver: webdriver.Chrome, timeout: int = 30):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def scrape_profile(self, url: str) -> Dict:
        """Извлекает данные из профиля Twitter, включая email"""
        result = {
            "url": url,
            "email_found": [],
            "profile_email": None,
            "website_url": None,
            "bio": None,
            "username": None,
            "name": None
        }

        try:
            # Открытие URL
            self.driver.get(url)
            
            # Ждем загрузки основного контента страницы
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']")))
            except TimeoutException:
                print(f"Timeout при ожидании загрузки основного контента {url}")
            
            # Извлечение имени пользователя и био
            try:
                # Имя
                name_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1 span")
                if name_elements:
                    result["name"] = name_elements[0].text.strip()
                
                # Username 
                username_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='UserName'] div[dir='ltr'] span")
                if not username_elements:
                    username_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[data-testid='UserName']")
                if username_elements:
                    for element in username_elements:
                        text = element.text.strip()
                        if text.startswith("@"):
                            result["username"] = text[1:]
                            break
                        elif '@' not in text and text:  # Только если это не email и не пустой текст
                            result["username"] = text
                            break
                        
                # Био
                bio_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='UserDescription']")
                if bio_elements:
                    result["bio"] = bio_elements[0].text
            
                # Поиск email в биографии профиля
                bio_text = result["bio"] if result["bio"] else ""
                profile_emails = self._extract_emails(bio_text)
                if profile_emails:
                    result["email_found"].extend(profile_emails)
                    result["profile_email"] = profile_emails[0]  # Первый найденный email
                    
            except Exception as e:
                print(f"Ошибка при извлечении данных профиля {url}: {str(e)}")
            
            # Извлечение веб-сайта (исключаем x.com/tos и другие внутренние ссылки)
            try:
                website_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='UserProfileHeader-websiteLink']")
                if website_elements:
                    for element in website_elements:
                        href = element.get_attribute("href")
                        # Исключаем внутренние ссылки X/Twitter
                        if (href and 
                            "http" in href and 
                            "@" not in href and  # Исключаем email из href
                            'x.com/tos' not in href and 
                            'twitter.com/tos' not in href and
                            'x.com/tos/terms' not in href and
                            'twitter.com/tos/terms' not in href):
                            result["website_url"] = href
                            break
                            
            except Exception as e:
                print(f"Ошибка при извлечении веб-сайта {url}: {str(e)}")
                
        except TimeoutException:
            print(f"Timeout при загрузке страницы {url}")
        
        return result

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