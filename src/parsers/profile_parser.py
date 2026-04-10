import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, List
import re


class TwitterProfileParser:
    def __init__(self, driver: WebDriver, timeout: int = 30):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def extract_profile_info(self) -> Dict:
        """Извлекает информацию из профиля Twitter"""
        profile_info = {
            "name": None,
            "username": None,
            "bio": None,
            "website_url": None,
            "location": None,
            "joined_date": None,
            "following_count": None,
            "followers_count": None,
            "tweets_count": None
        }

        try:
            # Ждем загрузки основного контента профиля
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='primaryColumn']")))
            
            # Имя пользователя (имя, которое отображается)
            try:
                name_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1 span")
                if name_elements:
                    profile_info["name"] = name_elements[0].text.strip()
            except Exception:
                pass

            # Username (никнейм после @)
            try:
                username_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='UserName'] span")
                if username_elements:
                    raw_username = username_elements[0].text.strip()
                    # Убираем символ @ если присутствует
                    if raw_username.startswith("@"):
                        profile_info["username"] = raw_username[1:]
                    else:
                        profile_info["username"] = raw_username
            except Exception:
                pass

            # Биография
            try:
                bio_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='UserDescription']")
                if bio_elements:
                    profile_info["bio"] = bio_elements[0].text.strip()
            except Exception:
                pass

            # Веб-сайт (улучшенная логика для фильтрации внутренних ссылок)
            try:
                website_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='UserProfileHeader-websiteLink']")
                for element in website_elements:
                    href = element.get_attribute("href")
                    # Исключаем внутренние ссылки X/Twitter
                    if href and 'x.com/tos' not in href and 'twitter.com/tos' not in href and 'x.com/privacy' not in href:
                        profile_info["website_url"] = href
                        break
            except Exception:
                pass

            # Местоположение
            try:
                location_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='UserProfileHeader-IssueLabel'] span")
                for element in location_elements:
                    text = element.text.strip()
                    # Предполагаем, что местоположение не является датой регистрации
                    if "Joined" not in text and text and len(text) < 50 and ',' in text or text.isalpha():
                        profile_info["location"] = text
                        break
            except Exception:
                pass

            # Дата регистрации
            try:
                joined_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='UserProfileHeader-IssueLabel'] span")
                for element in joined_elements:
                    text = element.text.strip()
                    if "Joined" in text:
                        profile_info["joined_date"] = text
                        break
            except Exception:
                pass

            # Счетчики: Твиты, подписки, подписчики
            try:
                # Ищем все ссылки с количеством (обычно они расположены в шапке профиля)
                counter_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/followers'], a[href*='/following'], a[href*='/with_replies']")
                
                # Обрабатываем каждую ссылку и определяем, что за счетчик
                for element in counter_elements:
                    href = element.get_attribute("href")
                    # Находим span с числом внутри ссылки
                    span_elements = element.find_elements(By.CSS_SELECTOR, "span")
                    
                    for span in span_elements:
                        text = span.text.strip()
                        # Проверяем, что текст содержит цифры (это потенциальный счетчик)
                        if text and any(char.isdigit() for char in text):
                            if '/following' in href:
                                profile_info["following_count"] = self.parse_count(text)
                            elif '/followers' in href or '/verified_followers' in href:
                                profile_info["followers_count"] = self.parse_count(text)
                            elif '/with_replies' in href or '/photo' in href or '/media' in href:
                                # Счетчик твитов (включая с медиа и с ответами)
                                profile_info["tweets_count"] = self.parse_count(text)
                
                # Если счетчики не были найдены по URL, пробуем определить по содержимому текста
                if (profile_info["following_count"] is None or 
                    profile_info["followers_count"] is None or 
                    profile_info["tweets_count"] is None):
                    
                    # Ищем все span с потенциальными числами в области профиля
                    all_spans = self.driver.find_elements(By.CSS_SELECTOR, "span")
                    for span in all_spans:
                        text = span.text.strip()
                        if text and any(char.isdigit() for char in text):
                            parent_element = span.find_element(By.XPATH, "./..")
                            parent_text = parent_element.text.lower()
                            
                            # Определяем тип счетчика по контексту
                            if 'follow' in parent_text and 'ing' in parent_text:
                                if profile_info["following_count"] is None:
                                    profile_info["following_count"] = self.parse_count(text)
                            elif 'follow' in parent_text and 'er' in parent_text:
                                if profile_info["followers_count"] is None:
                                    profile_info["followers_count"] = self.parse_count(text)
                            elif 'like' in parent_text or 'repost' in parent_text or 'share' in parent_text:
                                # Это не счетчик твитов, пропускаем
                                continue
                            else:
                                # Если невозможно определить контекст, и это большое число - возможно твиты
                                count_value = self.parse_count(text)
                                if count_value > 100 and profile_info["tweets_count"] is None:
                                    profile_info["tweets_count"] = count_value
                                
            except Exception as e:
                print(f"Ошибка при извлечении счетчиков: {str(e)}")

        except Exception as e:
            print(f"Ошибка при извлечении информации профиля: {str(e)}")

        return profile_info

    def parse_count(self, count_str: str) -> int:
        """Конвертирует строку с числом (например, '1.2K') в целое число"""
        if not count_str:
            return 0
        
        # Удаляем пробельные символы
        count_str = str(count_str).strip()
        
        if not count_str:
            return 0
            
        # Заменяем запятые и пробелы
        count_str = count_str.replace(',', '').replace(' ', '')
        
        # Если строка представляет собой число без сокращений
        if count_str.isdigit():
            return int(count_str)
        
        # Обработка сокращений
        count_str = count_str.upper()
        multiplier = 1
        
        if 'K' in count_str:
            multiplier = 1000
            count_str = count_str.replace('K', '')
        elif 'M' in count_str:
            multiplier = 1000000
            count_str = count_str.replace('M', '')
        elif 'B' in count_str:
            multiplier = 1000000000
            count_str = count_str.replace('B', '')
        
        try:
            return int(float(count_str) * multiplier)
        except ValueError:
            # Если не удалось распознать число, возвращаем 0
            return 0