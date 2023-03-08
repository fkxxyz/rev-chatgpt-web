# 由于 ChatGPT 一小时内请求过于频繁会导致429
# 故需要统计从任意时刻起的过去一小时的请求量，作为负载指标
import json
import threading
import time


class RequestCounter:
    def __init__(self, seconds: int, file: str):
        self.__length = seconds
        self.__loop_length = seconds * 2
        self.__file = file
        self.__locker = threading.Lock()
        self.__dirty = False

        self.__loop_counter = [0] * self.__loop_length
        self.__sum = 0
        self.__time = int(time.time())
        self.__load()
        self.__dirty = True
        threading.Thread(target=self.__run).start()

    def __run(self):
        while True:
            t_now = int(time.time())

            self.__locker.acquire()
            dirty = self.__dirty
            while self.__time <= t_now:
                i = (self.__time + self.__length) % self.__loop_length
                if self.__loop_counter[i] != 0:
                    dirty = True
                self.__sum -= self.__loop_counter[i]
                self.__loop_counter[i] = 0
                self.__time += 1
            self.__locker.release()

            if dirty:
                self.__save()
            time.sleep(1)

    def __save(self):
        self.__locker.acquire()
        s = json.dumps({
            "length": self.__length,
            "time": self.__time,
            "sum": self.__sum,
            "counter": self.__loop_counter,
        })
        self.__locker.release()
        with open(self.__file, 'w') as f:
            f.write(s)

    def __load(self):
        try:
            with open(self.__file, 'r') as f:
                s = f.read()
            s_json = json.loads(s)
            length = s_json["length"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return
        if length != self.__length:
            return
        t = s_json["time"]
        if self.__time - t >= self.__loop_length:
            return
        self.__time = t
        self.__sum = s_json["sum"]
        self.__loop_counter = s_json["counter"]

    def increase(self):
        i = int(time.time()) % self.__loop_length
        self.__locker.acquire()
        self.__loop_counter[i] += 1
        self.__sum += 1
        self.__dirty = True
        self.__locker.release()

    def get(self) -> int:
        return self.__sum
