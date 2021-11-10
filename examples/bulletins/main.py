from choixe.bulletins import Bulletin, BulletinBoard
import uuid
import numpy as np
import time
import threading
from rich.progress import Progress
import multiprocessing


###########################################################
###########################################################
###########################################################
# Install rabbitmq first!#
#
# sudo apt install rabbitmq-server
###########################################################
###########################################################
###########################################################

def fake_task(session_id: str, name: str):

    # Init
    total = 0
    board = BulletinBoard(session_id=session_id)

    while True:
        # random sleeop
        time.sleep(np.random.uniform(0.2, 0.5))

        # Random step
        step = np.random.randint(0, 10)
        board.hang(Bulletin(metadata={'name': name, 'step': step}))

        # update total
        total += step
        if total > 100:
            return


if __name__ == '__main__':

    tasks = {f'Task[{i}]': 0 for i in range(10)}
    session_id = str(uuid.uuid1())

    # Generate Fake Tasks processes
    for task_name, _ in tasks.items():
        multiprocessing.Process(target=fake_task, args=(session_id, task_name, )).start()

    # Bulletin update callback
    def bulletin_update(bulletin: Bulletin):
        global tasks
        tasks[bulletin.metadata['name']] += bulletin.metadata['step']

    # Central Node Thread waiting for new bulletins
    def central_node():
        main_board = BulletinBoard(session_id=session_id)
        main_board.register_callback(bulletin_update)
        main_board.wait_for_bulletins()

    threading.Thread(target=central_node, daemon=True).start()

    # Progress Bars update
    with Progress() as progress:

        # Generate bars
        bars = {name: progress.add_task(f"[green]{name}...", total=100) for name, _ in tasks.items()}

        # Update loop
        while not progress.finished:
            for task_name, value in tasks.items():
                progress.update(bars[task_name], completed=value)
