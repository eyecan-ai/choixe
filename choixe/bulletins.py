from typing import Callable, Sequence
import pika
import pickle


class Bulletin(object):

    def __init__(self, metadata: dict = None):
        self.metadata = metadata if metadata is not None else {}

    def to_bytes(self) -> bytes:
        return pickle.dumps(self)

    @classmethod
    def from_bytes(cls, b: bytes) -> 'Bulletin':
        return pickle.loads(b)


class BulletinBoard(object):

    def __init__(self, session_id: str, host: str = 'localhost') -> None:
        super().__init__()

        self._host = host
        self._sessionid = session_id
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(self._host))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue=self._sessionid)
        self._callbacks: Sequence[Callable] = []
        self._started = False

    def register_callback(self, cb: Callable):
        if len(self._callbacks) == 0:
            self._register_proxy()
        self._callbacks.append(cb)

    def hang(self, bulletin: Bulletin):
        self._channel.basic_publish(
            exchange='',
            routing_key=self._sessionid,
            body=bulletin.to_bytes()
        )

    def _register_proxy(self):
        self._channel.basic_consume(
            queue=self._sessionid,
            auto_ack=True,
            on_message_callback=self._callbacks_proxy
        )

    def _callbacks_proxy(self, ch, method, properties, body):
        bl = Bulletin.from_bytes(body)
        for cb in self._callbacks:
            cb(bl)

    def wait_for_bulletins(self):
        self._started = True
        self._channel.start_consuming()

    def close(self):
        # if self._started:
        self._channel.stop_consuming()
        # self._connection.close()
