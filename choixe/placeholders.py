

from enum import Enum, auto
from typing import Union
from choixe.directives import Directive, DirectiveConsumer, DirectiveFactory
from choixe.importers import Importer, ImporterType


class PlaceholderType(Enum):
    INT = auto()
    STR = auto()
    FLOAT = auto()
    BOOL = auto()
    PATH = auto()
    DATE = auto()
    ENV = auto()
    OBJECT = auto()
    CFG = auto()
    CFG_ROOT = auto()

    @classmethod
    def values(cls):
        return list([c.name.lower() for c in cls])

    @classmethod
    def get_type(cls, value: str) -> Union['PlaceholderType', None]:
        c = [x for x in value.split('(') if len(x) > 0]
        if len(c) > 0:
            v = c[0]
            return PlaceholderType[v.upper()]
        return None

    @classmethod
    def get_type_as_string(cls, value: str) -> str:
        tp = cls.get_type(value)
        if isinstance(tp, PlaceholderType):
            return tp.name
        return 'None'

    @classmethod
    def cast(cls, value: any, tp: 'PlaceholderType'):
        if tp == PlaceholderType.BOOL:
            return bool(value)
        elif tp == PlaceholderType.STR:
            return str(value)
        elif tp == PlaceholderType.INT:
            return int(value)
        elif tp == PlaceholderType.FLOAT:
            return float(value)
        elif tp == PlaceholderType.PATH:
            return value
        elif tp == PlaceholderType.DATE:
            return value
        elif tp == PlaceholderType.ENV:
            return str(value)
        elif tp == PlaceholderType.OBJECT:
            return value
        elif tp == PlaceholderType.CFG:
            return Importer.generate_importer_directive(ImporterType.IMPORT, value)
        elif tp == PlaceholderType.CFG_ROOT:
            return Importer.generate_importer_directive(ImporterType.IMPORT_ROOT, value)
        else:
            raise NotImplementedError(f'No cast for type [{tp}] on [{value}]')


class Placeholder(DirectiveConsumer):

    def __init__(self, directive: Directive):
        super().__init__(directive=directive)

    def is_valid(self):
        if self._directive.valid:
            return self._directive.label in PlaceholderType.values()
        return False

    @property
    def name(self):
        if self.is_valid():
            if len(self._directive.args) > 0:
                return self._directive.args[0]
        return None

    @property
    def options(self):
        if self.is_valid():
            return self._directive.args[1:]
        return []

    @property
    def default_value(self):
        if self.is_valid():
            return self._directive.default_value
        return None

    @property
    def plain_type(self):
        if self.is_valid():
            return PlaceholderType.get_type_as_string(self._directive.label)
        return PlaceholderType.get_type_as_string('')

    @property
    def type(self):
        if self.is_valid():
            return PlaceholderType.get_type(self._directive.label)
        return None

    def cast(self, value: any) -> any:
        return PlaceholderType.cast(value, self.type)

    @classmethod
    def from_string(cls, value: str) -> 'Placeholder':
        directive = DirectiveFactory.build_directive_from_string(value)
        if directive:
            return Placeholder(directive=directive)
        return None
