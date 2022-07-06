FROM ubuntu:20.04

RUN apt-get update -y
RUN apt install -y python3 python3-pip

WORKDIR /home/app

COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

COPY ./run.sh .
COPY ./src ./src

CMD ["./run.sh"]
