
import re
from abc import ABC


class Directive(ABC):

    @classmethod
    def generate_directive_string(cls, label: str, args: list = None) -> str:
        raise NotImplementedError

    @classmethod
    def directive_pattern(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def is_directive(cls, value: str) -> bool:
        matches = re.match(cls.directive_pattern(), str(value).strip())
        return matches is not None

    @classmethod
    def tokenize(cls, value: str) -> dict:
        raise NotImplementedError()

    @property
    def valid(self):
        return self._valid

    @property
    def label(self):
        return self._label

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def default_value(self):
        return self._default_value

    def __init__(self, value: str):
        if self.is_directive(value):
            self._valid = True
            self._tokens = self.tokenize(value)
            self._label = self._tokens['label'].lower()
            self._args = self._tokens['args']
            self._kwargs = self._tokens['kwargs']
            self._default_value = self._tokens['default_value']
        else:
            self._valid = False
            self._tokens = {}
            self._label = ''
            self._args = []
            self._kwargs = {}
            self._default_value = None


class DirectiveAT(Directive):
    DEFAULT_KEY = 'default'

    @classmethod
    def generate_directive_string(cls, label: str, args: list = None) -> str:
        if args is None:
            args = []
        return f'@{label}(' + ','.join(map(str, args)) + ')'

    @classmethod
    def directive_pattern(cls) -> str:
        return '[@].+[(](.+?)|[)]$'

    @classmethod
    def tokenize(cls, value: str) -> dict:
        value = value.strip()
        value = value.replace(' ', '')
        for ch in ['@', '(', ')']:
            value = value.replace(ch, ' ')
        values = value.split(' ')
        values = [x for x in values if len(x) > 0]
        assert len(values) >= 1

        label = values[0]
        args = values[1].split(',') if len(values) > 1 else []

        # default_token = f'{cls.DEFAULT_KEY}='

        kwargs = {}
        new_args = []
        for a in args:
            if '=' in a:
                key, value = [x.strip() for x in a.split('=')]
                kwargs[key] = value
            else:
                new_args.append(a)

        # # set default value if any
        default_value = None
        if cls.DEFAULT_KEY in kwargs:
            default_value = kwargs[cls.DEFAULT_KEY]

        return {
            'label': label,
            'args': new_args,
            'kwargs': kwargs,
            'default_value': default_value
        }


class DirectiveFactory(object):

    AVAILABLE_DIRECTIVES = [
        DirectiveAT
    ]

    @classmethod
    def build_directive_from_string(cls, value: str) -> Directive:
        for dtype in cls.AVAILABLE_DIRECTIVES:
            directive = dtype(value)
            if directive.valid:
                return directive
        return None


class DirectiveConsumer(object):

    def __init__(self, directive: Directive) -> None:
        self._directive = directive

    @property
    def directive(self):
        return self._directive

    @property
    def directive_class(self):
        return self._directive.__class__
