export PATH=$PATH:$HOME/.poetry/bin
echo "Starting tests ..."
poetry install
poetry run pytest tests/simple_test.py