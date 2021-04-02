from enum import Enum, auto
from typing import Union
from choixe.directives import Directive, DirectiveAT, DirectiveConsumer, DirectiveFactory


class ImporterType(Enum):
    IMPORT = auto()
    IMPORT_ROOT = auto()

    @classmethod
    def values(cls):
        return list([c.name.lower() for c in cls])

    @classmethod
    def get_type(cls, value: str) -> Union['ImporterType', None]:
        return ImporterType[value.upper()]


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

    @classmethod
    def generate_importer_directive(cls, importer_type: ImporterType, path: str):
        return DirectiveAT.generate_directive_string(str(importer_type.name).lower(), [path])
