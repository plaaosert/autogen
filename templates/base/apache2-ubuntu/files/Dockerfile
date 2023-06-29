FROM ubuntu:latest
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install apache2 -y
RUN apt-get install php -y
RUN apt-get install php-mysql -y
RUN apt-get install mysql-client -y
EXPOSE 80

RUN rm -rf /etc/apache2/sites-enabled/000-default.conf

COPY docker-entrypoint.sh /usr/local/bin/
RUN ["chmod", "+x", "/usr/local/bin/docker-entrypoint.sh"]

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

CMD ["apache2ctl", "-D", "FOREGROUND"]