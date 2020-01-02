FROM	fritzprix/cbuild:0.0.1

MAINTAINER	fritzprix

RUN	apt-get update
RUN	git clone https://github.com/fritzprix/jconfigpy.git
CMD python jconfigpy -s -i ./configs/config -t ./example/config.json