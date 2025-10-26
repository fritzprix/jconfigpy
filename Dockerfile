FROM	fritzprix/cbuild:0.0.1

MAINTAINER	fritzprix

RUN	apt-get update && apt-get install -y python3 python3-pip

WORKDIR	/jconfigpy

RUN	git clone https://github.com/fritzprix/jconfigpy.git /jconfigpy

RUN	pip3 install -e .

CMD	["python3", "-m", "jconfigpy", "-s", "-i", "./configs/config", "-t", "./example/config.json"]