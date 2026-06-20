# Настройка окружения

при добавлении новых зависимостей в pyproject.toml, перегенерить requirements.txt

``` bash
  cd python_syncworker
  python3.10 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip pip-tools
  pip-compile pyproject.toml -o requirements.txt 
```

при запуске юнит тестов из idea убедиться что выставлена следующая настройка

`Settings -> Tools -> Python Integrated Tools -> Testing -> Default test runner -> pytest`