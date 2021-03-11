
from choixe.bulletins import Bulletin, BulletinBoard
import uuid
import threading
import numpy as np
import time
import pytest
import pika

# @pytest.mark.rabbitmq


class TestBulletins(object):

    def test_multi_producer_sinle_consumer(self):

        session_id = str(uuid.uuid1())
        N = 10
        running = True
        try:
            main_board = BulletinBoard(session_id=session_id)
        except pika.exceptions.AMQPConnectionError:
            pytest.skip(msg=f'No rabbitmq server found!')
            return

        for i in range(N):
            board = BulletinBoard(session_id=session_id)
            board.hang(Bulletin(metadata={'value': np.random.randint(0, N)}))

        counter = 0

        def bulletin_update(bulletin: Bulletin):
            nonlocal counter
            assert 'value' in bulletin.metadata
            counter += 1
            print("COUNTER", counter, N)
            if counter >= N:
                main_board.close()

        main_board.register_callback(bulletin_update)
        main_board.wait_for_bulletins()
