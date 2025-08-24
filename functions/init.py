import os

def init():
    # data
    os.makedirs("data/official",exist_ok=True)
    os.makedirs("data/test",exist_ok=True)

    # image
    os.makedirs("image",exist_ok=True)

    # logs
    os.makedirs("logs",exist_ok=True)
