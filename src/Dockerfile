# pull official base image
FROM python:3.9.6-slim-buster

# set working directory
WORKDIR /usr/src

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc \
  && apt-get clean

# install python dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the ./app local directory inside the ./app working directory
COPY ./app ./app
