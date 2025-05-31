## RSS Parser

#### Как запустить проект

Создаем и активируем виртуальное окружение

```
python -m venv venv
source /venv/bin/activate
```

Подтягиваем зависимости

```
pip install -r requirements.txt
```


Запускаем проект

```
python rss_tracker.py
```


#### Эндпоинты

Сваггер можно найти по адресу 

```
http://localhost:8000/docs
```

Добавить источники для парсинга
```
http://localhost:8000/sources
```

```
{
  "url": "https://www.kommersant.ru/RSS/news.xml"
}
```

Добавить ключевые слова
```
http://localhost:8000/keyword
```

```
{
  "word": "Россия"
}
```

Итоговый список найденных новостей находится по адресу
```
http://localhost:8000/news
```