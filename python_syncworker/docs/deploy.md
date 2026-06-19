# Настройка окружения

При добавлении новых зависимостей в pyproject.toml, перегенерить requirements.txt

``` bash
  cd python_syncworker
  python3.10 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip pip-tools
  pip-compile pyproject.toml -o requirements.txt 
```