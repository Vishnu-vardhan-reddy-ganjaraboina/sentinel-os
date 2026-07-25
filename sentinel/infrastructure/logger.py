from sentinel.kernel.service import Service


class Logger(Service):

    def __init__(self):
        super().__init__("Logger")

    def start(self):

        print("Logger initialized.")

    def stop(self):

        print("Logger stopped.")