import os
from choixe.importers import Importer, ImporterType
from choixe.placeholders import Placeholder, PlaceholderType
from box.from_file import converters
from box import box_from_file, Box, BoxList
import numpy as np
import pydash
from typing import Any, Dict, List, Sequence, Tuple, Union
from schema import Schema
from pathlib import Path
import copy


class XConfig(Box):
    KNOWN_EXTENSIONS = converters.keys()
    PRIVATE_KEYS = ['_filename', '_schema']

    def __init__(self, filename: str = None, **kwargs):
        """ Creates a XConfig object from configuration file
        :param filename: configuration file [yaml, json, toml], defaults to None
        :type filename: str, optional
        :param replace_environment_variables: TRUE to auto replace environemnt variables placeholders, defaults to False
        :type replace_environment_variables: bool, optional
        :param plain_dict: if not None will be used as data source instead of filename, defaults to None
        :type plain_dict: dict, optional
        """

        # options
        replace_env_variables = kwargs.get('replace_environment_variables', True)
        _dict = kwargs.get('plain_dict', None)
        no_deep_parse = kwargs.get('no_deep_parse', False)

        self._filename = None

        if _dict is None:
            if filename is not None:
                self._filename = Path(filename)
                self.update(box_from_file(file=Path(filename)))
        else:
            self.update(_dict)

        self._schema = None

        if not no_deep_parse:
            self.deep_parse(replace_environment_variables=replace_env_variables)

    def copy(self) -> 'XConfig':
        """ Prototype copy

        :return: deep copy of source XConfig
        :rtype: XConfig
        """

        new_xconfig = XConfig(filename=None)
        new_xconfig.update(self.to_dict(discard_private_qualifiers=True))
        new_xconfig._filename = self._filename
        new_xconfig._schema = self._schema
        return new_xconfig

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

    def validate(self, replace: bool = True):
        """ Validate internal schema if any

        :param replace: TRUE to replace internal dictionary with force-validated fields (e.g. Schema.Use)
        :type replace: bool
        """

        if self.get_schema() is not None:
            new_dict = self.get_schema().validate(self.to_dict())
            if replace:
                self.update(new_dict)

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
        data = self.to_dict()
        if 'yml' in filename.suffix.lower() or 'yaml' in filename.suffix.lower():
            Box(self.decode(data)).to_yaml(filename=filename)
        elif 'json' in filename.suffix.lower():
            Box(self.decode(data)).to_json(filename=filename)
        elif 'toml' in filename.suffix.lower():
            Box(self.decode(data)).to_toml(filename=filename)
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
        elif isinstance(data, list) or isinstance(data, BoxList):
            return [cls.decode(x) for x in data]
        elif isinstance(data, tuple):
            return [cls.decode(x) for x in data]
        elif isinstance(data, dict) or isinstance(data, Box):
            return {k: cls.decode(x) for k, x in data.items()}
        else:
            return data

    def chunks_as_lists(self, discard_private_qualifiers: bool = True) -> Sequence[Tuple[List[str], Any]]:
        """ Builds a plain view of dictionary with pydash list of str notation
        :param discard_private_qualifiers: TRUE to discard keys starting with private qualifier, defaults to True
        :type discard_private_qualifiers: bool, optional
        :return: list of pairs (key, value) where key is a list of str pydash key
        (e.g. d['one']['two']['three'] -> ['one', 'two', 'three'] )
        :rtype: Sequence[Tuple[List[str], Any]]
        """
        return self._walk(self, discard_private_qualifiers=discard_private_qualifiers)

    def chunks_as_tuples(self, discard_private_qualifiers: bool = True) -> Sequence[Tuple[Tuple[str, ...], Any]]:
        """ Builds a plain view of dictionary with pydash tuple of str notation
        :param discard_private_qualifiers: TRUE to discard keys starting with private qualifier, defaults to True
        :type discard_private_qualifiers: bool, optional
        :return: list of pairs (key, value) where key is a tuple of str pydash key
        (e.g. d['one']['two']['three'] -> ('one', 'two', 'three') )
        :rtype: Sequence[Tuple[Tuple[str, ...], Any]]
        """
        return [(tuple(x), y) for x, y in self._walk(self, discard_private_qualifiers=discard_private_qualifiers)]

    def chunks(self, discard_private_qualifiers: bool = True) -> Sequence[Tuple[str, Any]]:
        """ Builds a plain view of dictionary with pydash dot notation
        :param discard_private_qualifiers: TRUE to discard keys starting with private qualifier, defaults to True
        :type discard_private_qualifiers: bool, optional
        :return: list of pairs (key, value) where key is a dot notation pydash key (e.g. d['one']['two']['three'] -> 'one.two.three' )
        :rtype: Sequence[Tuple[str, Any]]
        """

        return [('.'.join(x), y) for x, y in self.chunks_as_lists(discard_private_qualifiers=discard_private_qualifiers)]

    def is_a_placeholder(self, value: any) -> bool:
        """ Checks if value is likely a placeholder

        :param value: input value to check (e.g. '$hello')
        :type value: any
        :return: TRUE if value is a placeholder
        :rtype: bool
        """
        if not isinstance(value, str):
            return False
        placeholder = Placeholder.from_string(value)
        if placeholder:
            return placeholder.is_valid()
        return False

    def deep_set(self, full_key: Union[str, list], value: any, only_valid_keys: bool = True):
        """ Sets value based on full path key (dot notation like 'a.b.0.d' or list ['a','b','0','d'])

        :param full_key: full path key as dotted string or list of chunks
        :type full_key: str | list
        :param value: value to set
        :type value: any
        :param only_valid_keys: TRUE to avoid set on not present keys
        :type only_valid_keys: bool
        """

        if only_valid_keys:
            if pydash.has(self, full_key):
                pydash.set_(self, full_key, value)
        else:
            pydash.set_(self, full_key, value)

    def deep_update(self, other: 'XConfig', full_merge: bool = False):
        """ Updates current confing in depth, based on keys of other input XConfig.
        It is used to replace nested keys with new ones, but can also be used as a merge
        of two completely different XConfig if `full_merge`=True


        :param other: other XConfig to use as data source
        :type other: XConfig
        :param full_merge: FALSE to replace only the keys that are actually present
        :type full_merge: bool
        """

        other_chunks = other.chunks_as_lists(discard_private_qualifiers=True)
        for key, new_value in other_chunks:
            self.deep_set(key, new_value, only_valid_keys=not full_merge)

    def replace_variable(self, old_value: str, new_value: str):
        """ Replaces target variables with custom new value
        :param old_value: value to replace
        :type old_value: str
        :param new_value: new key value
        :type new_value: str
        """
        chunks = self.chunks_as_lists(discard_private_qualifiers=True)
        for k, v in chunks:
            p = Placeholder.from_string(v)
            if p is not None and p.is_valid():
                if old_value == p.name:
                    pydash.set_(self, k, p.cast(new_value))

    def replace_variables_map(self, m: dict):
        """ Replace target old variables with new values represented as dict
        :param m: dict of key/value = old/new
        :type m: dict
        """

        for old_v, new_v in m.items():
            self.replace_variable(old_v, new_v)

    def deep_parse(self, replace_environment_variables: bool = False):
        """ Deep visit of dictionary replacing filename values with a new XConfig object recusively

        :param replace_environment_variables: TRUE to auto replace environment variables
        :type replace_environment_variables: bool
        """
        chunks = self.chunks_as_lists()
        self._deep_parse_for_importers(chunks)
        if replace_environment_variables:
            self._deep_parse_for_environ(chunks)

    def _deep_parse_for_importers(self, chunks: Sequence[Tuple[Union[str, list], Any]]):
        """ Deep visit of dictionary replacing filename values with a new XConfig object recusively

        :param chunks: chunks to visit
        :type chunks: Sequence[Tuple[Union[str, list], Any]]
        :raises NotImplementedError: Importer type not found
        :raises OSError: replace file not found
        """

        for chunk_name, value in chunks:
            if not isinstance(value, str):
                continue
            importer = Importer.from_string(value)
            if importer is not None:
                if importer.is_valid():

                    p = Path(importer.path)
                    if self._filename is not None and not p.is_absolute():
                        p = self._filename.parent / p

                    if p.exists():
                        self._import_external_file(importer, chunk_name, p)
                    else:
                        raise OSError(f'File {p} not found!')

    def _import_external_file(self, importer: Importer, chunk_name: Union[str, list], filename: Path):
        """ Imports a generic file into cfg tree

        :param importer: importer directive
        :type importer: Importer
        :param chunk_name: chunk name (dotted str or list of keys) to replace
        :type chunk_name: Union[str, list]
        :param filename: external filename to import
        :type filename: Path
        :raises NotImplementedError: if importer type is not managed yet
        :raises RuntimeError: if external file content is not readable
        """

        extension = filename.suffix.replace('.', '')
        if extension in self.KNOWN_EXTENSIONS:
            sub_cfg = XConfig(filename=filename)
            if importer.type == ImporterType.IMPORT_ROOT:
                pydash.set_(self, chunk_name, sub_cfg.root_content)
            elif importer.type == ImporterType.IMPORT:
                pydash.set_(self, chunk_name, sub_cfg)
            else:
                raise NotImplementedError(f"Importer type {importer.type} not implemented yet!")
        else:
            try:
                content = open(filename, 'r').read()
                pydash.set_(self, chunk_name, content)
            except UnicodeDecodeError:
                raise RuntimeError(f'Error reading content of file: {str(filename)}. Is this a binary file?')

    def _deep_parse_for_environ(self, chunks: Sequence[Tuple[Union[str, list], Any]]):
        """ Deep visit of dictionary replacing environment variables if any

        :param chunks: chunks to visit
        :type chunks: Sequence[Tuple[Union[str, list], Any]]
        :raises NotImplementedError: Importer type not found
        :raises OSError: replace file not found
        """

        env_to_replace = {}
        for chunk_name, value in chunks:
            if not isinstance(value, str):
                continue
            placeholder = Placeholder.from_string(value)
            if placeholder is not None:
                if placeholder.is_valid():
                    if placeholder.type == PlaceholderType.ENV:
                        if placeholder.name in os.environ:
                            env_to_replace[placeholder.name] = os.environ.get(placeholder.name)

        self.replace_variables_map(env_to_replace)

    def to_dict(self, discard_private_qualifiers: bool = True) -> Dict:
        """
        Turn the Box and sub Boxes back into a native python dictionary.
        :return: python dictionary of this Box
        """
        out_dict = copy.deepcopy(dict(self))
        for k, v in out_dict.items():
            if isinstance(v, Box):
                out_dict[k] = self.decode(v.to_dict())
            elif isinstance(v, BoxList):
                out_dict[k] = self.decode(v.to_list())

        if discard_private_qualifiers:
            chunks = self.chunks_as_lists(discard_private_qualifiers=False)
            for key, value in chunks:
                if any([x for x in self.PRIVATE_KEYS if x in key]):
                    pydash.unset(out_dict, key)

        return out_dict

    def available_placeholders(self) -> Dict[str, Placeholder]:
        """ Retrieves the available placeholders list

        :return: list of found (str,str) pairs
        :rtype: Tuple[str,str]
        """

        chunks = self.chunks_as_tuples(discard_private_qualifiers=True)
        placeholders = {}
        for k, v in chunks:
            if self.is_a_placeholder(v):
                key = '.'.join(k)
                placeholders[key] = Placeholder.from_string(v)
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
            table.add_column("Placeholder", style="dim")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Options")
            table.add_column("Default")

            header = "*** Incomplete Configuration, Placeholders found! ***"
            rich.print(Markdown(f"# {header}"))

            for k, p in placeholders.items():
                if p.is_valid():
                    table.add_row(k, p.name, p.plain_type, '|'.join(p.options), p.default_value)

            console.print(table)

            if close_app:
                import sys
                sys.exit(1)
            return False
        return True

    @classmethod
    def from_dict(cls, d: dict, **kwargs) -> 'XConfig':
        """ Creates XConfig from a plain dictionary
        : param d: input dictionary
        : type d: dict
        : return: built XConfig
        : rtype: XConfig
        """
        cfg = XConfig(filename=None, plain_dict=d, **kwargs)
        return cfg

    @classmethod
    def _add_key_to_path(cls, key_to_add: any, path: Sequence[any]):
        path.append(str(key_to_add))

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
                cls._add_key_to_path(k, path)
                if isinstance(v, dict) or isinstance(v, list):
                    cls._walk(
                        v,
                        path=path,
                        chunks=chunks,
                        discard_private_qualifiers=discard_private_qualifiers
                    )
                else:
                    keys = list(map(str, path))
                    if not(discard_private_qualifiers and any([x for x in cls.PRIVATE_KEYS if x in keys])):
                        chunks.append((keys, v))
                path.pop()
        elif isinstance(d, list):
            for idx, v in enumerate(d):
                cls._add_key_to_path(idx, path)
                cls._walk(
                    v,
                    path=path,
                    chunks=chunks,
                    discard_private_qualifiers=discard_private_qualifiers
                )
                path.pop()
        else:
            keys = list(map(str, path))
            chunks.append((keys, d))
        if root:
            return chunks
