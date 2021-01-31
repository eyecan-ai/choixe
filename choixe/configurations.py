from enum import Enum, auto
from box.from_file import converters
from box import box_from_file, Box, BoxList
import numpy as np
import pydash
from typing import Any, Dict, Sequence, Tuple, Union
from schema import Schema
from pathlib import Path
import re


class XPlaceholderType(Enum):
    INT = auto()
    STR = auto()
    FLOAT = auto()
    BOOL = auto()
    PATH = auto()
    OPTIONS = auto()
    DATE = auto()

    # @classmethod
    # def validate(cls, value: any, tp: str):
    #     tp = cls.get_type(tp)
    #     if tp is not None:
    #         tp: XPlaceholderType
    #         if tp == XPlaceholderType.INT:
    #             return isinstance(value, int)
    #         elif tp == XPlaceholderType.FLOAT:
    #             return isinstance(value, float)
    #         elif tp == XPlaceholderType.STR:
    #             return isinstance(value, str)
    #         elif tp == XPlaceholderType.BOOL:
    #             return isinstance(value, bool)

    #     return False

    @classmethod
    def get_type(cls, value: str) -> Union['XPlaceholderType', None]:
        c = [x for x in value.split('(') if len(x) > 0]
        if len(c) > 0:
            v = c[0]
            return XPlaceholderType[v.upper()]
        return None

    @classmethod
    def get_type_as_string(cls, value: str) -> str:
        tp = cls.get_type(value)
        if isinstance(tp, XPlaceholderType):
            return tp.name
        return 'None'


class XPlaceholder(object):

    def __init__(self, value: any, qualifier: str):
        self.value = value
        self._qualifier = qualifier
        self.chunks = self.get_placeholder_chunks()

    def is_valid(self):
        if isinstance(self.value, str):
            return self.value.startswith(self._qualifier)
        return False

    @property
    def base(self):
        if self.is_valid():
            return self.chunks[0]
        return None

    @property
    def base_with_qualifier(self):
        if self.is_valid():
            return f'{self._qualifier}{self.chunks[0]}'
        return None

    @property
    def plain_type(self):
        if self.is_valid():
            if len(self.chunks) > 1:
                return XPlaceholderType.get_type_as_string(f'{self.chunks[1]}')
        return XPlaceholderType.get_type_as_string('')

    @property
    def type(self):
        if self.is_valid():
            if len(self.chunks) > 1:
                return XPlaceholderType.get_type(f'{self.chunks[1]}')
        return None

    def get_placeholder_chunks(self) -> Union[Sequence[str], None]:
        """ Retrieves placeholder chunks if any. E.g. $name$options(1,2,3)
        will return (name, options(1,2,3))

        :return: None if value is not a placeholder, otherwise a Sequence of strings
        :rtype: Union[Sequence[str], None]
        """
        if self.is_valid():
            chunks = [c for c in re.split(f'\\{self._qualifier}', self.value) if len(c) > 0]
            return chunks
        return []

    def __eq__(self, p: 'XPlaceholder') -> bool:
        if self.is_valid() and p.is_valid():
            return self.base == p.base
        return False


class XConfig(Box):
    PRIVATE_QUALIFIER = '_'
    REFERENCE_QUALIFIER = '@'
    REPLACE_QUALIFIER = '$'
    KNOWN_EXTENSIONS = converters.keys()

    def __init__(self, filename: str = None):
        """ Creates a XConfig object from configuration file
        :param filename: configuration file [yaml, json, toml], defaults to None
        :type filename: str, optional
        """
        self._filename = None
        if filename is not None:
            self._filename = Path(filename)
            self.update(box_from_file(file=Path(filename)))
        self._schema = None
        self.deep_parse()

    @property
    def root_content(self) -> Union[None, Any]:
        """ Returns the 'value' if configuration is a single 'key'/'value' pair.
        Otherwise None
        :return: 'value' if configuration is a single 'key'/'value' pair. Otherwise None
        :rtype: Union[None, Any]
        """
        d = self.to_dict(discard_private_qualifiers=True)
        if len(d.keys()) == 1:
            return d[list(d.keys())[0]]
        return None

    def get_schema(self):
        return self._schema

    def set_schema(self, s: Schema):
        """ Push validation schema
        :param schema: validation schema
        :type schema: Schema
        """
        if s is not None:
            assert isinstance(s, Schema), "schema is not a valid Schema object!"
        self._schema: Schema = s

    def validate(self):
        """ Validate internal schema if any """
        if self.get_schema() is not None:
            self.get_schema().validate(self.to_dict())

    def is_valid(self) -> bool:
        """ Check for schema validity
        :return: TRUE for valid or no schema inside
        :rtype: bool
        """
        if self.get_schema() is not None:
            return self.get_schema().is_valid(self.to_dict())
        return True

    def save_to(self, filename: str):
        """ Save configuration to output file
        :param filename: output filename
        :type filename: str
        :raises NotImplementedError: Raise error for unrecognized extension
        """
        filename = Path(filename)
        if 'yml' in filename.suffix.lower() or 'yaml' in filename.suffix.lower():
            Box(self.decode(self.to_dict())).to_yaml(filename=filename)
        elif 'json' in filename.suffix.lower():
            Box(self.decode(self.to_dict())).to_json(filename=filename)
        elif 'toml' in filename.suffix.lower():
            Box(self.decode(self.to_dict())).to_toml(filename=filename)
        else:
            raise NotImplementedError(f"Extension {filename.suffix.lower()} not supported yet!")

    @classmethod
    def decode(cls, data: any) -> any:
        """ Decode decodable data

        :param data: [description]
        :type data: any
        :return: [description]
        :rtype: any
        """
        if isinstance(data, np.ndarray):
            return cls.decode(data.tolist())
        elif 'numpy' in str(type(data)):
            return cls.decode(data.item())
        elif isinstance(data, list):
            return [cls.decode(x) for x in data]
        elif isinstance(data, dict):
            return {k: cls.decode(x) for k, x in data.items()}
        elif isinstance(data, Box):
            return cls.decode(data.to_dict())
        elif isinstance(data, BoxList):
            return cls.decode(data.to_list())
        else:
            return data

    def chunks(self, discard_private_qualifiers: bool = True) -> Sequence[Tuple[str, Any]]:
        """ Builds a plain view of dictionary with pydash notation
        :param discard_private_qualifiers: TRUE to discard keys starting with private qualifier, defaults to True
        :type discard_private_qualifiers: bool, optional
        :return: list of pairs (key, value) where key is a dot notation pydash key (e.g. d['one']['two']['three'] -> 'one.two.three' )
        :rtype: Sequence[Tuple[str, Any]]
        """
        return self._walk(self, discard_private_qualifiers=discard_private_qualifiers)

    def is_a_placeholder(self, value: any) -> bool:
        """ Checks if value is likely a placeholder

        :param value: input value to check (e.g. '$hello')
        :type value: any
        :return: TRUE if value is a placeholder
        :rtype: bool
        """
        if isinstance(value, str):
            return value.startswith(self.REPLACE_QUALIFIER)
        else:
            return False

    def deep_set(self, full_key: str, value: any):
        """ Sets value based on full path key (dot notation like 'a.b.0.d')

        :param full_key: full path key
        :type full_key: str
        :param value: value to set
        :type value: any
        """

        pydash.set_(self, full_key, value)

    def replace(self, old_value: str, new_value: str):
        """ Replaces target value with custom new value
        :param old_value: value to replace
        :type old_value: str
        :param new_value: new key value
        :type new_value: str
        """
        old_placeholder = XPlaceholder(old_value, self.REPLACE_QUALIFIER)
        if old_placeholder.is_valid():
            chunks = self.chunks(discard_private_qualifiers=True)
            for k, v in chunks:
                p = XPlaceholder(v, qualifier=self.REPLACE_QUALIFIER)
                if p.is_valid():
                    if old_placeholder == p:
                        # chunks = self.get_placeholder_chunks(v)
                        # if chunks is not None:
                        #     if f'{self.REPLACE_QUALIFIER}{chunks[0]}' == old_value:
                        pydash.set_(self, k, new_value)

    def replace_map(self, m: dict):
        """ Replace target old values with new values represented as dict
        :param m: dict of key/value = old/new
        :type m: dict
        """

        for old_v, new_v in m.items():
            self.replace(old_v, new_v)

    def deep_parse(self):
        """ Deep visit of dictionary replacing filename values with a new XConfig object recusively
        """
        chunks = self.chunks()
        for chunk_name, value in chunks:
            if self._could_be_path(value):
                n_references = value.count(self.REFERENCE_QUALIFIER)
                p = Path(value.replace(self.REFERENCE_QUALIFIER, ''))
                if self._filename is not None and not p.is_absolute():
                    p = self._filename.parent / p

                if p.exists():
                    sub_cfg = XConfig(filename=p)
                    # if sub_cfg.root_content is not None:
                    #     pydash.set_(self, chunk_name, sub_cfg.root_content)
                    # else:
                    if n_references == 2:
                        pydash.set_(self, chunk_name, sub_cfg.root_content)
                    elif n_references == 1:
                        pydash.set_(self, chunk_name, sub_cfg)
                    else:
                        raise NotImplementedError(f"Number of {self.REFERENCE_QUALIFIER} is wrong!")
                else:
                    raise OSError(f'File {p} not found!')

    def _could_be_path(self, p: str) -> bool:
        """ Check if a string could be a path. It's not a robust test outside XConfig!
        :param p: source string
        :type p: str
        :return: TRUE = 'maybe is path'
        :rtype: bool
        """
        if isinstance(p, str):
            if any(f'.{x}{self.REFERENCE_QUALIFIER}' in p for x in self.KNOWN_EXTENSIONS):
                return True
        return False

    def to_dict(self, discard_private_qualifiers: bool = True) -> Dict:
        """
        Turn the Box and sub Boxes back into a native python dictionary.
        :return: python dictionary of this Box
        """
        out_dict = dict(self)
        for k, v in out_dict.items():
            if v is self:
                out_dict[k] = out_dict
            elif isinstance(v, Box):
                out_dict[k] = v.to_dict()
            elif isinstance(v, BoxList):
                out_dict[k] = v.to_list()

        if discard_private_qualifiers:
            chunks = self.chunks(discard_private_qualifiers=False)
            for chunk_name, value in chunks:
                if f'.{self.PRIVATE_QUALIFIER}' in chunk_name or chunk_name.startswith(self.PRIVATE_QUALIFIER):
                    pydash.unset(out_dict, chunk_name)
        return out_dict

    def available_placeholders(self) -> Sequence[Tuple[str, str]]:
        """ Retrieves the available placeholders list
        :return: list of found (str,str) pairs
        :rtype: Tuple[str,str]
        """

        chunks = self.chunks(discard_private_qualifiers=True)
        placeholders = []
        for k, v in chunks:
            if self.is_a_placeholder(v):
                placeholders.append((k, XPlaceholder(v, qualifier=self.REPLACE_QUALIFIER)))
        return placeholders

    def check_available_placeholders(self, close_app: bool = False) -> bool:
        """ Check for available placeholder and close app if necessary
        :param close_app: TRUE to close app if at least one placeholder found, defaults to False
        :type close_app: bool, optional
        :return: TRUE if no placeholders found
        :rtype: bool
        """
        placeholders = self.available_placeholders()
        if len(placeholders) > 0:
            import rich
            from rich.table import Table
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            table = Table(show_header=True, header_style='bold magenta')
            table.add_column("Name", style="dim")
            table.add_column("Placeholder")
            table.add_column("Type")

            header = "*** Incomplete Configuration, Placeholders found! ***"
            rich.print(Markdown(f"# {header}"))

            for k, p in placeholders:
                if p.is_valid():
                    table.add_row(k, p.base_with_qualifier, p.plain_type)

            console.print(table)

            if close_app:
                import sys
                sys.exit(1)
            return False
        return True

    @classmethod
    def from_dict(cls, d: dict) -> 'XConfig':
        """ Creates XConfig from a plain dictionary
        : param d: input dictionary
        : type d: dict
        : return: built XConfig
        : rtype: XConfig
        """
        cfg = XConfig()
        cfg.update(Box(d))
        return cfg

    @classmethod
    def _walk(cls,
              d: Dict, path: Sequence = None,
              chunks: Sequence = None,
              discard_private_qualifiers: bool = True) -> Sequence[Tuple[str, Any]]:
        """ Deep visit of dictionary building a plain sequence of pairs(key, value) where key has a pydash notation
        : param d: input dictionary
        : type d: Dict
        : param path: private output value for path(not use), defaults to None
        : type path: Sequence, optional
        : param chunks: private output to be fileld with retrieved pairs(not use), defaults to None
        : type chunks: Sequence, optional
        : param discard_private_qualifiers: TRUE to discard keys starting with private qualifier, defaults to True
        : type discard_private_qualifiers: bool, optional
        : return: sequence of retrieved pairs
        : rtype: Sequence[Tuple[str, Any]]
        """
        root = False
        if path is None:
            path, chunks, root = [], [], True
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, dict) or isinstance(v, list):
                    path.append(k)
                    cls._walk(v, path=path, chunks=chunks, discard_private_qualifiers=discard_private_qualifiers)
                    path.pop()
                else:
                    path.append(k)
                    chunk_name = ".".join(map(str, path))
                    if not(discard_private_qualifiers and chunk_name.startswith(cls.PRIVATE_QUALIFIER)):
                        chunks.append((chunk_name, v))
                    path.pop()
        elif isinstance(d, list):
            for idx, v in enumerate(d):
                path.append(str(idx))
                cls._walk(v, path=path, chunks=chunks, discard_private_qualifiers=discard_private_qualifiers)
                path.pop()
        if root:
            return chunks
