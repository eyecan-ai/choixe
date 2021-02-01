from enum import Enum, auto
from typing import Union
from choixe.directives import Directive, DirectiveConsumer, DirectiveFactory
from pathlib import Path


class ImporterType(Enum):
    IMPORT = auto()
    IMPORT_ROOT = auto()

    @classmethod
    def values(cls):
        return list([c.name.lower() for c in cls])

    @classmethod
    def get_type(cls, value: str) -> Union['ImporterType', None]:
        return ImporterType[value.upper()]

    # @classmethod
    # def get_type_as_string(cls, value: str) -> str:
    #     tp = cls.get_type(value)
    #     if isinstance(tp, ImporterType):
    #         return tp.name
    #     return 'None'


class Importer(DirectiveConsumer):

    def __init__(self, directive: Directive):
        super().__init__(directive=directive)

    def is_valid(self):
        if self._directive.valid:
            return self._directive.label in ImporterType.values()
        return False

    @property
    def path(self):
        if self.is_valid():
            if len(self._directive.args) > 0:
                return self._directive.args[0]
        return ''

    @property
    def type(self):
        if self.is_valid():
            return ImporterType.get_type(self._directive.label)
        return None

    @classmethod
    def from_string(cls, value: str) -> 'Importer':
        directive = DirectiveFactory.build_directive_from_string(value)
        if directive:
            return Importer(directive=directive)
        return None
