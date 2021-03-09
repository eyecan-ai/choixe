
from functools import wraps
import typing
from abc import ABC
from schema import Schema


class Spook(ABC):
    # 👻👻👻👻👻👻👻👻👻👻👻👻👻👻

    TYPE_FIELD = '__spook__'
    ARGS_FIELD = 'args'
    SPOOKS_MAP = {}

    @classmethod
    def spook_name(cls) -> str:
        return cls.__name__

    @classmethod
    def full_spook_schema(cls) -> Schema:
        return Schema({
            Spook.TYPE_FIELD: cls.spook_name(),
            Spook.ARGS_FIELD: cls.spook_schema()
        })

    @classmethod
    def spook_schema(cls) -> typing.Union[None, dict]:
        return None

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def to_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def _validate_schema(cls, d: dict):
        if cls.spook_schema() is not None:
            cls.full_spook_schema().validate(d)

    def serialize(self, validate: bool = True) -> dict:
        out = {
            Spook.TYPE_FIELD: self.spook_name(),
            Spook.ARGS_FIELD: self.to_dict()
        }
        if validate:
            self._validate_schema(out)
        return out

    @classmethod
    def hydrate(cls, d: dict, validate: bool = True) -> any:
        """ Hydrate dict in order to re-create the correspoding Spook

        :param d: serialized dict
        :type d: dict
        :param validate: TRUE to validate dict schema before hydratation, defaults to False
        :type validate: bool, optional
        :return: hydrated object
        :rtype: any
        """
        if validate:
            cls._validate_schema(d)
        return cls.from_dict(d[Spook.ARGS_FIELD])

    @classmethod
    def register_spook(cls, x: type):
        """ Register a Spook in the factory map

        :param x: target class to register. It must be a Spook!
        :type x: Spook
        """
        cls.SPOOKS_MAP[x.spook_name()] = x

    @classmethod
    def create(cls, d: dict, validate: bool = True) -> any:
        """ Creates an object starting from its serialized dict.
        It must be a Spook serialized class containing all deserialization attributes

        :param d: serialized dict
        :type d: dict
        :param validate: TRUE to validate dict schema before hydratation, defaults to False
        :type validate: bool, optional
        :raises RuntimeError: when corresponding class is not registered in the factory map
        :return: hydrated object
        :rtype: any
        """
        if d[Spook.TYPE_FIELD] in cls.SPOOKS_MAP:
            bt = cls.SPOOKS_MAP[d[Spook.TYPE_FIELD]]
            return bt.hydrate(d, validate=validate)
        raise RuntimeError(f'Non serializable data: {d}')

    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻
    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻
    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻
    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻

    @staticmethod
    def make_serializable(x: type):
        Spook.register_spook(x)
        return x

    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻
    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻
    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻
    # 🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻🤟🏻
