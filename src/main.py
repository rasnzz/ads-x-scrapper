import os
import time
import yaml
from dotenv import load_dotenv
from typing import List, Dict
import argparse

from adspower_client import AdsPowerClient
from scraper import connect_to_profile, TwitterEmailScraper
from parsers.profile_parser import TwitterProfileParser
from parsers.website_parser import WebsiteParser
from email_extractor import EmailExtractor
from exporters.csv_exporter import CSVExporter
from utils.logger import setup_logger
from utils.rate_limiter import RateLimiter


def load_config(config_path: str = "config/config.yaml") -> Dict:
    """Загружает конфигурацию из YAML файла"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def read_urls(input_file: str) -> List[str]:
    """Читает URL из файла"""
    with open(input_file, 'r', encoding='utf-8') as file:
        urls = [line.strip() for line in file if line.strip()]
    return urls


def process_twitter_profile(scraper: TwitterEmailScraper, 
                          profile_parser: TwitterProfileParser, 
                          website_parser: WebsiteParser,
                          url: str,
                          delay: float,
                          logger) -> Dict:
    """Обрабатывает один Twitter профиль"""
    result = {
        "url": url,
        "email_found": [],
        "profile_email": None,
        "website_url": None,
        "bio": None,
        "username": None,
        "name": None,
        "location": None,
        "joined_date": None,
        "following_count": None,
        "followers_count": None,
        "tweets_count": None,
        "external_emails": []
    }

    try:
        logger.info(f"Обработка профиля: {url}")
        
        # Переходим напрямую на URL профиля
        scraper.driver.get(url)
        
        # Ждем немного для загрузки страницы
        time.sleep(3)
        
        # Извлекаем информацию из профиля с помощью обоих методов и объединяем
        # Сначала используем профайл-парсер
        logger.info("Извлечение данных через profile_parser")
        profile_info = profile_parser.extract_profile_info()
        logger.info(f"Данные от profile_parser: {profile_info}")
        
        # Потом используем скрапер
        logger.info("Извлечение данных через scraper")
        scraper_data = scraper.scrape_profile(url)
        logger.info(f"Данные от scraper: {scraper_data}")
        
        # Объединяем результаты, проверяя на пустые значения
        def get_first_valid(*values):
            """Возвращает первое непустое значение из списка"""
            for value in values:
                if value is not None and value != '' and str(value).strip() != '':
                    return value
            return None

        result.update({
            "bio": get_first_valid(profile_info.get("bio"), scraper_data.get("bio")),
            "username": get_first_valid(profile_info.get("username"), scraper_data.get("username")),
            "name": get_first_valid(profile_info.get("name"), scraper_data.get("name")),
            "location": get_first_valid(profile_info.get("location")),
            "joined_date": get_first_valid(profile_info.get("joined_date")),
            "following_count": get_first_valid(profile_info.get("following_count")),
            "followers_count": get_first_valid(profile_info.get("followers_count")),
            "tweets_count": get_first_valid(profile_info.get("tweets_count")),
            "website_url": get_first_valid(profile_info.get("website_url"), scraper_data.get("website_url"))
        })
        
        # Извлекаем email из всех доступных источников
        all_emails = set(result["email_found"])  # Избегаем дубликатов
        
        # Email из биографии профиля
        bio_text = result["bio"] or ""
        profile_emails = scraper._extract_emails(bio_text)
        all_emails.update(profile_emails)
        
        # Email из данных скрапера
        scraper_emails = scraper_data.get("email_found", [])
        all_emails.update(scraper_emails)
        
        if profile_emails:
            result["profile_email"] = profile_emails[0]
        
        result["email_found"] = list(all_emails)
        
        logger.info(f"Объединенный результат до посещения сайта: {result}")
        
        # Если найден веб-сайт во внешнем профиле, посещаем его
        website_url = result.get("website_url")
        if website_url:
            logger.info(f"Посещение внешнего сайта: {website_url}")
            
            try:
                scraper.driver.get(website_url)
                
                # Ждем немного для загрузки страницы
                time.sleep(2)
                
                # Извлекаем email с внешнего сайта
                external_emails = website_parser.extract_emails_from_page()
                result["external_emails"] = external_emails
                result["email_found"].extend(external_emails)
                
                logger.info(f"Найденные email на внешнем сайте: {external_emails}")
                
            except Exception as e:
                logger.warning(f"Ошибка при посещении внешнего сайта {website_url}: {str(e)}")
            
            # Возвращаемся к профилю Twitter и даем время на загрузку
            scraper.driver.get(url)
            time.sleep(3)
        
        # Задержка между обработкой профилей
        time.sleep(delay)
        
        logger.info(f"Успешно обработан профиль: {url}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {str(e)}")
        
        # Добавляем информацию об ошибке в результат
        result["error"] = str(e)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Скрапер Twitter для извлечения email адресов")
    parser.add_argument("--config", default="config/config.yaml", help="Путь к файлу конфигурации")
    args = parser.parse_args()
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Загружаем конфигурацию
    config = load_config(args.config)
    api_key = os.getenv("ADSPOWER_API_KEY")
    
    if not api_key:
        raise ValueError("Не найден ADSPOWER_API_KEY в переменных окружения")
    
    # Настройка логирования
    logger = setup_logger()
    
    # Инициализация компонентов
    client = AdsPowerClient(config["adspower"]["api_base_url"], api_key)
    exporter = CSVExporter(config["scraper"]["output_dir"])
    rate_limiter = RateLimiter(max_requests=2, time_window=1)  # Ограничение 2 запроса в секунду
    
    logger.info("Начало работы скрапера Twitter")
    
    # Запуск профиля AdsPower
    logger.info("Запуск профиля AdsPower...")
    start_data = client.start_profile(config["adspower"]["user_id"], config["adspower"]["headless"])
    selenium_endpoint = start_data["ws"]["selenium"]
    
    # Подключение к браузеру
    logger.info(f"Подключение к браузеру через {selenium_endpoint}...")
    driver = connect_to_profile(selenium_endpoint)
    
    # Инициализация скрапера и парсеров
    scraper = TwitterEmailScraper(driver, config["scraper"]["timeout_seconds"])
    profile_parser = TwitterProfileParser(driver, config["scraper"]["timeout_seconds"])
    website_parser = WebsiteParser(driver, config["scraper"]["timeout_seconds"])
    
    try:
        # Чтение URL из входного файла
        logger.info(f"Чтение URL из файла {config['scraper']['input_file']}...")
        urls = read_urls(config["scraper"]["input_file"])
        
        # Ограничиваем количество URL если задано в конфиге
        if config["scraper"]["max_urls"] > 0:
            urls = urls[:config["scraper"]["max_urls"]]
        
        logger.info(f"Найдено {len(urls)} URL для обработки")
        
        results = []
        
        # Обработка каждого URL
        for i, url in enumerate(urls, 1):
            logger.info(f"Обработка {i}/{len(urls)}: {url}")
            
            # Применяем ограничение скорости
            rate_limiter.wait_if_needed()
            
            result = process_twitter_profile(
                scraper=scraper,
                profile_parser=profile_parser,
                website_parser=website_parser,
                url=url,
                delay=config["scraper"]["delay_between_urls"],
                logger=logger
            )
            
            results.append(result)
        
        # Экспорт результатов
        logger.info("Экспорт результатов...")
        output_file = exporter.export_results(results)
        logger.info(f"Результаты экспортированы в {output_file}")
        
    finally:
        # Закрытие всех вкладок и остановка профиля AdsPower
        logger.info("Закрытие всех вкладок и остановка профиля AdsPower...")
        
        # Закрываем все вкладки кроме первой
        try:
            while len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])  # переключаемся на последнюю вкладку
                driver.close()  # закрываем её
                
            # Переключаемся обратно на первую вкладку
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
        except:
            pass  # Если не удается закрыть вкладки, просто продолжаем
        
        # Останавливаем профиль AdsPower
        client.stop_profile(config["adspower"]["user_id"])
        driver.quit()
        
        logger.info("Скрипт завершен")


if __name__ == "__main__":
    main()