curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
poetry install
poetry run pytest tests/simple_test.py