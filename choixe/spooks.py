from __future__ import annotations
from abc import ABCMeta

import typing
from schema import Schema
from choixe.configurations import XConfig


class MetaSpook(ABCMeta):
    # 😱😱😱😱😱😱😱😱😱😱😱😱😱😱
    SPOOKS_MAP = {}

    def __init__(self, name, bases, dict) -> None:
        MetaSpook.register_spook(self)

    @classmethod
    def clear_factory(cls):
        cls.SPOOKS_MAP = {}

    @classmethod
    def register_spook(cls, x: typing.Type[Spook]):
        """Register a Spook in the factory map

        :param x: target class to register. It must be a Spook!
        :type x: Type[Spook]
        """
        cls.SPOOKS_MAP[x.spook_name()] = x


class Spook(metaclass=MetaSpook):
    # 👻👻👻👻👻👻👻👻👻👻👻👻👻👻

    TYPE_FIELD = "__spook__"
    ARGS_FIELD = "args"

    @classmethod
    def spook_name(cls) -> str:
        # return cls.__name__
        return f"{cls.__module__}.{cls.__name__}"

    @classmethod
    def full_spook_schema(cls) -> Schema:
        return Schema(
            {Spook.TYPE_FIELD: cls.spook_name(), Spook.ARGS_FIELD: cls.spook_schema()}
        )

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
        out = {Spook.TYPE_FIELD: self.spook_name(), Spook.ARGS_FIELD: self.to_dict()}
        if validate:
            self._validate_schema(out)
        return out

    def serialize_to_file(self, path: str, validate: bool = True):
        serialization = self.serialize(validate=validate)
        cfg = XConfig.from_dict(serialization)
        cfg.save_to(path)

    @classmethod
    def hydrate(cls, d: dict, validate: bool = True) -> any:
        """Hydrate dict in order to re-create the correspoding Spook

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
    def dynamic_import(cls, full_name: str) -> typing.Any:
        """Dynamic import of full qualified name (module....ClassName)

        :param full_name: full qualified name
        :type full_name: str
        :return: imported class/function
        :rtype: typing.Any
        """
        components = full_name.split(".")
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    @classmethod
    def create_from_file(cls, filename: str) -> any:
        """Creates an object starting from its serialized representation in a file loadable
        as XConfig (yml, json, etc.)

        :param filename: config filename
        :type filename: str
        :return: hydrated object
        :rtype: any
        """
        return cls.create(XConfig(filename))

    @classmethod
    def create(cls, d: dict, validate: bool = True) -> any:
        """Creates an object starting from its serialized dict.
        It must be a Spook serialized class containing all deserialization attributes

        :param d: serialized dict
        :type d: dict
        :param validate: TRUE to validate dict schema before hydratation, defaults to False
        :type validate: bool, optional
        :raises RuntimeError: when corresponding class is not registered in the factory map
        :return: hydrated object
        :rtype: any
        """
        if d[Spook.TYPE_FIELD] not in cls.SPOOKS_MAP:
            try:
                cls.SPOOKS_MAP[d[Spook.TYPE_FIELD]] = cls.dynamic_import(
                    d[Spook.TYPE_FIELD]
                )
            except Exception as e:
                raise RuntimeError(
                    f"SPOOK ALERT! Unable to import {d[Spook.TYPE_FIELD]} class: {e}"
                )

        if d[Spook.TYPE_FIELD] in cls.SPOOKS_MAP:
            bt = cls.SPOOKS_MAP[d[Spook.TYPE_FIELD]]
            return bt.hydrate(d, validate=validate)
        raise RuntimeError(f"Non serializable data: {d}")
