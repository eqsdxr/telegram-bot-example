A telegram bot for reading RSS feeds built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot).

Project highlights:
- Uses MongoDB for data storage
- Dockerized for easy deployment
- Includes unit tests
- Implements RSS functionality using [feedparser](https://pypi.org/project/feedparser/) library

![screenshot](assets/screenshot.jpg)

# How to run
- Fill variables in .env:
```python
copy .env.example .env
```
## Run in docker
- Build:
```python
docker build -t telegram-bot .
```
- Run:
```python
docker run \
  --rm \
  --env .env
  telegram-bot
```
## Run locally
- Install dependencies:
```python
uv venv && uv source .venv/bin/activate
```
- Run
```
python -m app.main
```
