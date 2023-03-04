# 由于 ChatGPT 一小时内请求过于频繁会导致429
# 故需要统计从任意时刻起的过去一小时的请求量，作为负载指标

import threading
import time


class RequestCounter:
    def __init__(self, seconds: int):
        self.__length = seconds
        self.__loop_length = seconds * 2
        self.__loop_counter = [0] * self.__loop_length
        self.__sum = 0
        self.__locker = threading.Lock()
        threading.Thread(target=self.__run).start()

    def __run(self):
        while True:
            i = (int(time.time()) + self.__length) % self.__loop_length
            self.__locker.acquire()
            self.__sum -= self.__loop_counter[i]
            self.__loop_counter[i] = 0
            self.__locker.release()
            time.sleep(1)

    def increase(self):
        i = int(time.time()) % self.__loop_length
        self.__locker.acquire()
        self.__loop_counter[i] += 1
        self.__sum += 1
        self.__locker.release()

    def get(self) -> int:
        return self.__sum
