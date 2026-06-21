from abc import ABC, abstractmethod


class BaseMonitor(ABC):
    name: str = ""

    @abstractmethod
    def snapshot(self) -> dict:
        ...

    @abstractmethod
    def display(self) -> None:
        ...
