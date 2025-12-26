"""
 SnowflakeIDGenerator 类用于生成分布式唯一 ID，基于 Twitter 的 Snowflake 算法实现。
 该算法通过组合时间戳、工作节点 ID 和序列号生成全局唯一的 64 位整数 ID。
 具有以下特性：
 - 时间戳部分表示生成 ID 的时间，精确到毫秒。
 - 工作节点 ID 可以标识不同机器或实例。
 - 序列号用于处理同一毫秒内生成的多个 ID。

 参数说明:
 - worker_id: 表示工作节点的 ID，默认为 1。
 - datacenter_id: 表示数据中心的 ID，默认为 1。

 主要方法:
 - generate(): 生成一个唯一的 ID。
 - _time_gen(): 获取当前时间的时间戳（毫秒）。
 - _wait_for_next_millis(last_timestamp): 等待直到下一毫秒，防止重复生成相同 ID。

 注意事项:
 - 如果系统时间回拨（时间被往回调整），可能会抛出异常。
 - 生成的 ID 是单调递增的，但不保证完全连续。
"""



import time
import threading


class SnowflakeIDGenerator:
    def __init__(self, worker_id=1, datacenter_id=1):
        # 自定义起始时间戳（毫秒）
        self.epoch = 1704067200000  # 2024-01-01

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.sequence_bits = 12

        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.sequence_mask = -1 ^ (-1 << self.sequence_bits)

        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits

        if self.worker_id > self.max_worker_id or self.datacenter_id > self.max_datacenter_id:
            raise ValueError("worker_id 或 datacenter_id 超出范围")

    def _time_gen(self):
        return int(time.time() * 1000)

    def _wait_for_next_millis(self, last_timestamp):
        timestamp = self._time_gen()
        while timestamp <= last_timestamp:
            timestamp = self._time_gen()
        return timestamp

    def generate(self):
        with self.lock:
            timestamp = self._time_gen()

            if timestamp < self.last_timestamp:
                raise Exception("系统时间回拨，拒绝生成 ID")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.sequence_mask
                if self.sequence == 0:
                    timestamp = self._wait_for_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return ((timestamp - self.epoch) << self.timestamp_shift) | \
                   (self.datacenter_id << self.datacenter_id_shift) | \
                   (self.worker_id << self.worker_id_shift) | \
                   self.sequence
