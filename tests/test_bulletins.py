
from choixe.bulletins import Bulletin, BulletinBoard
import uuid
import numpy as np
import pytest
import pika


class TestBulletins(object):

    def test_multi_producer_sinle_consumer(self):

        session_id = str(uuid.uuid1())
        connections = 10
        # running = True
        try:
            main_board = BulletinBoard(session_id=session_id)
        except pika.exceptions.AMQPConnectionError:
            pytest.skip(msg='No rabbitmq server found!')
            return

        for i in range(connections):
            board = BulletinBoard(session_id=session_id)
            board.hang(Bulletin(metadata={'value': np.random.randint(0, connections)}))

        counter = 0

        def bulletin_update(bulletin: Bulletin):
            nonlocal counter
            assert 'value' in bulletin.metadata
            counter += 1
            print("COUNTER", counter, connections)
            if counter >= connections:
                main_board.close()

        main_board.register_callback(bulletin_update)
        main_board.wait_for_bulletins()
