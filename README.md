# Ainahack-2024 backend

## Setup
1. Inside your python environment of choice, install poetry
```sh
pip install poetry
```
2. Run it with uvicorn
```sh
cd backend
poetry run uvicorn app.main:app --reload
```

**Alternatively** if you have docker installed, run the docker image:
```sh
docker run -it $(docker build -q .)
```

