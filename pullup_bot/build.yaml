ARG BUILD_FROM
FROM $BUILD_FROM

# Встановлюємо Python та необхідні пакети
RUN apk add --no-cache python3 py3-pip

# Копіюємо скрипт бота
COPY run.sh /run.sh
RUN chmod a+x /run.sh

COPY pull_up /pull_up

# Встановлюємо залежності Python
RUN pip3 install --no-cache-dir -r /pull_up/requirements.txt

CMD ["/run.sh"]
