from enum import Enum, auto
from typing import Union
from choixe.directives import (
    Directive,
    DirectiveConsumer,
    DirectiveFactory,
)


class SweeperType(Enum):
    SWEEP = auto()

    @classmethod
    def values(cls):
        return list([c.name.lower() for c in cls])

    @classmethod
    def get_type(cls, value: str) -> Union["SweeperType", None]:
        return SweeperType[value.upper()]


class Sweeper(DirectiveConsumer):
    def __init__(self, directive: Directive):
        super().__init__(directive=directive)

    def is_valid(self):
        if self._directive.valid:
            return self._directive.label in SweeperType.values()
        return False

    @classmethod
    def from_string(cls, value: str) -> "Sweeper":
        directive = DirectiveFactory.build_directive_from_string(value)
        if directive:
            return Sweeper(directive=directive)
        return None

    @property
    def options(self):
        if self.is_valid():
            return self._directive.args[:]
        return []
