FROM python:3
ENV PYTHONUNBUFFERED 1
COPY . /HANDLER
WORKDIR /HANDLER
RUN pip3 install --upgrade pip
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
COPY . /tmp/