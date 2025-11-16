from abc import ABC, abstractmethod


class BaseMiddleware(ABC):
    def __init__(self):
        self.connection = None

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the message broker"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the message broker"""
        pass
