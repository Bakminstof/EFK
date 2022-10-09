import json
import ssl
import threading
import time
import urllib
import requests
import logging

logging.basicConfig(
    level='DEBUG',
    format='%(levelname)s | %(name)s | %(asctime)s | %(lineno)s | %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S',
)
logger = logging.getLogger('logs_getter')

# SERVER_LOGS_URL = 'http://10.18.0.40:5000/api/logs'  ## dev ##
SERVER_LOGS_URL = 'https://45.141.103.27:443/api/logs'
SEND_LOGS_URL = 'http://fluentd_l:6969/'


class LogsGetter:
    def __init__(self, timeout: int = 6):
        self.timeout = timeout
        self.first = 1
        self.fluent_json = {'foo': 'bar'}
        self.headers = {'content-type': 'application/json'}
        self.fluent_match = 'bot_mk_1.log'
        self.log_data = []
        self.lock = threading.Lock()
        self.url_to_send = SEND_LOGS_URL + self.fluent_match

    def _get_logs(self) -> None:
        try:
            logger.debug('Start getting data')

            url_for_get = SERVER_LOGS_URL + f'?first={self.first}'

            ssl._create_default_https_context = ssl._create_unverified_context

            response = urllib.request.urlopen(url_for_get, timeout=self.timeout)

            text = response.read().decode('UTF-8')
            data = json.loads(text)

            if len(data) > 0:
                if self.first:
                    self.first = 0

                with self.lock:
                    self.log_data.append(data)
                    logger.debug('Data added')

                logger.info(f'Get data: {len(data)} records')

            logger.debug('End getting data')

        except Exception as e:
            logger.error(e)
            time.sleep(self.timeout + 2)

        finally:
            time.sleep(3)

    def _send_log_data(self) -> None:
        with self.lock:
            logger.debug('Start sending data')

            for part in self.log_data:
                for _ in range(1, 5):
                    try:
                        response = requests.post(
                            url=self.url_to_send,
                            json=json.dumps(self.fluent_json),
                            timeout=self.timeout,
                            data=json.dumps(part),
                            headers=self.headers
                        )
                        if response.status_code == 200:
                            logger.debug('Send data')
                            break
                        else:
                            raise Exception(f'Can\'t send, status code: {response.status_code}')

                    except Exception as e:
                        logger.error(e)
                        time.sleep(self.timeout + 2)
                        continue
                else:
                    raise Exception(f'Can\' send')
            else:
                self.log_data.clear()

        logger.debug('End sending data')

    def start(self):
        while True:
            get_Thread = threading.Thread(target=self._get_logs)
            send_Thread = threading.Thread(target=self._send_log_data)

            get_Thread.start()
            send_Thread.start()

            get_Thread.join()
            send_Thread.join()

            del get_Thread, send_Thread


getter = LogsGetter()
getter.start()
