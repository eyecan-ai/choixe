import rich
import pytest
from schema import Or, SchemaError
from choixe.spooks import Spook


class SimpleUserObject__(Spook):

    def __init__(
        self,
        a: int,
        b: str,
        c: bool
    ) -> None:
        super().__init__()
        self.a = a
        self.b = b
        self.c = c

    def __eq__(self, o: object) -> bool:
        return \
            self.a == o.a and \
            self.b == o.b and \
            self.c == o.c


class CustomUserObject__(Spook):

    def __init__(
        self,
        a: int = None,
        b: str = None,
        c: bool = None
    ) -> None:
        super().__init__()
        self._misc = (a, b, c)

    @classmethod
    def spook_schema(cls) -> dict:
        return {
            'a': Or(None, int),
            'b': Or(None, str),
            'c': Or(None, bool)
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            a=d['a'],
            b=d['b'],
            c=d['c']
        )

    def to_dict(self) -> dict:
        return {
            'a': self._misc[0],
            'b': self._misc[1],
            'c': self._misc[2],
        }

    def __eq__(self, o: object) -> bool:
        return \
            self._misc[0] == o._misc[0] and \
            self._misc[1] == o._misc[1] and \
            self._misc[2] == o._misc[2]


class NestedUserObject_(Spook):

    def __init__(self, name: str, o0: SimpleUserObject__, o1: SimpleUserObject__):
        self._name = name
        self._o0 = o0
        self._o1 = o1

    @classmethod
    def spook_schema(cls) -> dict:
        return {
            'name': str,
            'o0': dict,
            'o1': dict
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            name=d['name'],
            o0=Spook.create(d['o0']),
            o1=Spook.create(d['o1'])
        )

    def to_dict(self) -> dict:
        return {
            'name': self._name,
            'o0': self._o0.serialize(),
            'o1': self._o1.serialize(),
        }

    def __eq__(self, o: object) -> bool:
        return \
            self._name == o._name and \
            self._o0 == o._o0 and \
            self._o1 == o._o1


class TestSpookSimpleSerialization(object):

    def test_simple_serialization(self):

        # args_list = [
        #     {'a': 666, 'b': 'hello!', 'c': True},
        #     {'a': None, 'b': None, 'c': None},
        # ]
        items_list = [
            {'kwargs': {'a': 666, 'b': 'hello!', 'c': True}, 'valid': True},
            {'kwargs': {'a': 'error!', 'b': 'hello!', 'c': True}, 'valid': False},
            {'kwargs': {'a': 66.6, 'b': 'hello!', 'c': True}, 'valid': False},
            {'kwargs': {'a': None, 'b': 'hello!', 'c': True}, 'valid': True},
        ]

        for item in items_list:
            kwargs = item['kwargs']
            valid = item['valid']
            print(valid)
            o_0 = SimpleUserObject__(**kwargs)
            rep_0 = o_0.serialize()

            o_1 = Spook.create(rep_0)
            assert isinstance(o_1, SimpleUserObject__)
            rep_1 = o_1.serialize()

            assert o_1 == o_0
            print(rep_0, rep_1)


class TestSpookCustomSerialization(object):

    def test_custom_serialization(self):

        items_list = [
            {'kwargs': {'a': 666, 'b': 'hello!', 'c': True}, 'valid': True},
            {'kwargs': {'a': 'error!', 'b': 'hello!', 'c': True}, 'valid': False},
            {'kwargs': {'a': 66.6, 'b': 'hello!', 'c': True}, 'valid': False},
            {'kwargs': {'a': None, 'b': 'hello!', 'c': True}, 'valid': True},
        ]

        for item in items_list:
            kwargs = item['kwargs']
            valid = item['valid']
            o_0 = CustomUserObject__(**kwargs)

            if valid:
                rep_0 = o_0.serialize(validate=True)
            else:
                with pytest.raises(SchemaError):
                    rep_0 = o_0.serialize(validate=True)
                continue

            o_1 = Spook.create(rep_0, validate=True)
            assert isinstance(o_1, CustomUserObject__)
            rep_1 = o_1.serialize(validate=True)
            print(rep_1)
            assert o_1 == o_0


class TestSpookNestedSerialization(object):

    def test_nested_serialization(self):

        items_list = [
            {
                'kwargs': {
                    'name': 'n0',
                    'o0': {'a': 1, 'b': 'hello', 'c': True},
                    'o1': {'a': 2, 'b': 'world!', 'c': False}
                },
                'valid': True
            },
            {
                'kwargs': {
                    'name': 'n0',
                    'o0': {'a': 'error!', 'b': 'world!', 'c': False},
                    'o1': {'a': 2, 'b': 'world!', 'c': False}
                },
                'valid': False
            },
        ]

        for item in items_list:
            kwargs = item['kwargs']
            valid = item['valid']

            o0 = CustomUserObject__(**kwargs['o0'])
            o1 = CustomUserObject__(**kwargs['o1'])
            name = kwargs['name']

            nested_0 = NestedUserObject_(name=name, o0=o0, o1=o1)

            if valid:
                rep_0 = nested_0.serialize(validate=True)
                rich.print("Representaiton", rep_0)
                nested_1 = Spook.create(rep_0)
                assert nested_0 == nested_1
            else:
                with pytest.raises(SchemaError):
                    nested_0.serialize(validate=True)
