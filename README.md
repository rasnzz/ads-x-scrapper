# Twitter Email Scraper с использованием AdsPower

Скрипт для извлечения публичных email адресов из профилей Twitter (X) с использованием локального API антидетект-браузера AdsPower.

## Особенности

- Использует AdsPower для анонимного скрапинга Twitter
- Запускает один профиль AdsPower на всю сессию
- Открывает вкладки для каждого профиля и закрывает после обработки
- Извлекает email адреса из профиля Twitter и с внешних сайтов
- Сохраняет результаты в CSV формате

## Установка

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd twitter-email-scraper
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Установите и запустите AdsPower:
- Убедитесь, что AdsPower клиент запущен на локальной машине
- Локальный API должен быть доступен по адресу http://local.adspower.net:50325

## Настройка

1. Скопируйте `.env.example` в `.env` и добавьте ваш API ключ:
```bash
cp .env.example .env
```
Отредактируйте `.env` и добавьте ваш API ключ:
```
ADSPOWER_API_KEY=ваш_api_ключ_здесь
```

2. Настройте `config/config.yaml`:
```yaml
adspower:
  api_base_url: "http://local.adspower.net:50325"
  user_id: "39"  # ID вашего профиля в AdsPower
  headless: false

scraper:
  input_file: "data/input.txt"  # Файл с URL профилей Twitter
  output_dir: "data/output"     # Каталог для сохранения результатов
  output_format: "csv"
  max_urls: 0                   # Максимальное количество URL для обработки (0 - без ограничений)
  delay_between_urls: 5         # Задержка между обработкой профилей (в секундах)
  timeout_seconds: 30           # Таймаут ожидания загрузки страниц
  close_extra_tabs: true        # Закрывать дополнительные вкладки
```

3. Подготовьте список URL профилей Twitter в файле `data/input.txt`, по одному URL на строку:
```
https://twitter.com/username1
https://twitter.com/username2
https://twitter.com/username3
```

## Использование

Запустите скрипт:
```bash
python src/main.py
```

Для использования другого файла конфигурации:
```bash
python src/main.py --config=path/to/your/config.yaml
```

## Структура проекта

```
├── src/
│   ├── __init__.py
│   ├── main.py                 # Главный исполняемый модуль
│   ├── adspower_client.py      # Класс для работы с API AdsPower
│   ├── scraper.py              # Основной класс TwitterEmailScraper
│   ├── email_extractor.py      # Регулярки и валидация email
│   ├── parsers/
│   │   ├── profile_parser.py   # Извлечение данных профиля Twitter
│   │   └── website_parser.py   # Поиск email на внешнем сайте
│   ├── utils/
│   │   ├── logger.py           # Настройка логирования
│   │   └── rate_limiter.py     # Ограничение скорости запросов
│   └── exporters/
│       └── csv_exporter.py     # Экспорт результатов в CSV
├── data/
│   ├── input.txt               # Входные URL
│   └── output/                 # Результаты
├── config/
│   ├── config.yaml             # Конфигурационный файл
│   └── .env.example            # Пример файла окружения
├── requirements.txt
└── README.md
```

## Результаты

Результаты сохраняются в каталоге `data/output` в формате CSV. Имя файла включает метку времени. Файл содержит следующие колонки:

- `url`: URL профиля Twitter
- `email_found`: Найденные email адреса (через запятую)
- `profile_email`: Первый найденный email в профиле
- `website_url`: URL внешнего сайта из профиля
- `bio`: Биография пользователя
- `username`: Имя пользователя (никнейм)
- `name`: Отображаемое имя
- `location`: Местоположение
- `joined_date`: Дата регистрации
- `following_count`: Количество подписок
- `followers_count`: Количество подписчиков
- `tweets_count`: Количество твитов
- `external_emails`: Email адреса с внешнего сайта
- `error`: Описание ошибки (если возникла)

## Ограничения

- Скрипт работает на бесплатном тарифе AdsPower, что накладывает ограничения на частоту запросов (до 2 запросов в секунду при <=200 профилей)
- Работа возможна только с публичными профилями Twitter
- Email адреса должны быть указаны в профиле или на внешнем сайте