import pandas as pd
import os
from typing import List, Dict
from datetime import datetime


class CSVExporter:
    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_results(self, results: List[Dict], filename: str = None):
        """Экспортирует результаты в CSV файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"twitter_emails_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Преобразуем результаты в формат подходящий для DataFrame
        processed_results = []
        for result in results:
            processed_result = {}
            for key, value in result.items():
                if isinstance(value, list):
                    # Конвертируем списки в строку с разделением запятыми
                    processed_result[key] = ', '.join(map(str, value))
                else:
                    # Обрабатываем строковые значения, заменяя переводы строк и специальные символы
                    if isinstance(value, str):
                        # Заменяем переводы строк на символы новой строки или на пробел
                        processed_result[key] = value.replace('\n', ' ').replace('\r', ' ').strip()
                    else:
                        processed_result[key] = value
            processed_results.append(processed_result)
        
        # Создаем DataFrame и сохраняем в CSV
        df = pd.DataFrame(processed_results)
        # Используем двойные кавычки для экранирования полей с запятыми и переводами строк
        df.to_csv(filepath, index=False, encoding='utf-8', quoting=1)  # quoting=1 означает csv.QUOTE_ALL
        
        return filepath