from typing import Union
import copy
from box.box_list import BoxList
import numpy as np
from box.box import Box
from deepdiff import DeepDiff
from schema import Schema, Or, Regex, SchemaMissingKeyError

import pydash
from pathlib import Path
import pytest
from choixe.configurations import XConfig, XPlaceholder


@pytest.fixture(scope="function")
def generic_temp_folder(tmpdir_factory):
    fn = tmpdir_factory.mktemp("_choixe_temp_folder")
    return fn


def simple_data():
    sample_dict = {
        'one': 1,
        'two': np.random.randint(-50, 50, (3, 3)).tolist(),
        'three': {
            'a': 2,
            'c': True
        }
    }
    schema = Schema(
        {
            'one': Or(int, str),
            'two': list,
            'three': {
                'a': int,
                'c': bool
            }
        }
    )

    to_be_raplaced_keys = sorted([
        'three'
    ], reverse=True)

    return sample_dict, schema, [], to_be_raplaced_keys


def generate_placeholder(name: str, tp: str = None, qualifier: str = XConfig.REPLACE_QUALIFIER):
    if tp is not None:
        if len(tp) > 0:
            return f'{qualifier}{name}{qualifier}{tp}'
    return f'{qualifier}{name}'


def complex_data():
    np.random.seed(666)

    placeholders = [
        generate_placeholder('v_0', 'int'),
        generate_placeholder('v_1', 'float'),
        generate_placeholder('v_2', 'str'),
        generate_placeholder('v_3', 'bool'),
        generate_placeholder('v_4', 'options("a","b","c")'),
        generate_placeholder('v_5', 'path'),
        generate_placeholder('v_6', 'date'),
        generate_placeholder('v_7'),
        generate_placeholder('v_8'),
        generate_placeholder('v_9'),
    ]
    # placeholders = [
    #     f'{XConfig.REPLACE_QUALIFIER}v_0',
    #     f'{XConfig.REPLACE_QUALIFIER}v_1',
    #     f'{XConfig.REPLACE_QUALIFIER}v_2',
    #     f'{XConfig.REPLACE_QUALIFIER}v_3'
    # ]

    sample_dict = {
        'one': placeholders[0],
        'two': np.random.randint(-50, 50, (3, 3)).tolist(),
        'three': {
            '3.1': True,
            '2.1': [False, False],
            'name': {
                'name_1': placeholders[1],
                'name_2': 2,
                'name_3': {
                    'this_is_a_list': [3.3, 3.3],
                    'this_is_A_dict': {
                        'a': {'f': True, 's': False}
                    }
                }
            }
        },
        'first': {
            'f1': placeholders[2],
            'f2': 2.22,
            'f3': [3, 3, 3, 3, 3, 3],
            'external': {
                'ext': np.random.uniform(-2, 2, (2, 3)).tolist(),
                'ext_name': placeholders[3],
            },
            'ops': {
                'o1': placeholders[4],
                'o2': placeholders[5],
                'o3': placeholders[6],
                'o4': placeholders[7],
                'o5': placeholders[8],
                'o6': placeholders[9]
            }
        }
    }

    schema = Schema(
        {
            'one': Or(int, str),
            'two': list,
            'three': {
                '3.1': bool,
                '2.1': [bool],
                'name': dict
            },
            'first': {
                Regex(''): Or(str, int, list, float, dict)
            }
        }
    )

    to_be_raplaced_keys = sorted([
        'three.name',
        'three.name.name_3',
        'three.name.name_3.this_is_A_dict',
        'first',
        'first.external'
    ], reverse=True)

    return sample_dict, schema, placeholders, to_be_raplaced_keys


def data_to_test():
    return [
        simple_data(),
        complex_data()
    ]


def store_cfg(filename: Union[str, Path], d: dict):

    filename = str(filename)
    data = Box(d)
    if 'yml' in filename or 'yaml' in filename:
        data.to_yaml(filename)
    if 'json' in filename:
        data.to_json(filename)
    if 'toml' in filename:
        data.to_toml(filename)


class TestXConfig(object):

    @pytest.mark.parametrize("cfg_extension", ['yaml', 'json', 'toml'])
    @pytest.mark.parametrize("data", data_to_test())
    def test_creation(self, generic_temp_folder, data, cfg_extension):  # TODO: toml 0.10.2 needed! toml has a bug otherwise

        generic_temp_folder = Path(generic_temp_folder)

        sample_dict, _, _, to_be_raplaced_keys = data
        volatile_dict = copy.deepcopy(sample_dict)

        subtitutions_values = {}
        for k in to_be_raplaced_keys:
            random_name = k + f".{cfg_extension}{XConfig.REFERENCE_QUALIFIER}"
            subtitutions_values[random_name] = pydash.get(volatile_dict, k)

            subtitutions_values[random_name]
            pydash.set_(volatile_dict, k, random_name)

        output_cfg_filename = generic_temp_folder / f'out_config.{cfg_extension}'
        output_cfg_filename2 = generic_temp_folder / f'out_config2.{cfg_extension}'

        subtitutions_values[str(output_cfg_filename)] = volatile_dict

        saved_cfgs = []
        for output_filename, d in subtitutions_values.items():
            output_filename = generic_temp_folder / output_filename.replace(f'{XConfig.REFERENCE_QUALIFIER}', '')
            store_cfg(output_filename, d)
            saved_cfgs.append(output_filename)

        yconf = XConfig(output_cfg_filename)
        yconf.save_to(output_cfg_filename2)
        yconf_reloaded = XConfig(output_cfg_filename2)

        assert not DeepDiff(yconf.to_dict(), sample_dict)
        assert not DeepDiff(yconf_reloaded.to_dict(), sample_dict)
        assert not DeepDiff(XConfig.from_dict(yconf_reloaded.to_dict()).to_dict(), yconf_reloaded.to_dict())
        assert len(XConfig.from_dict(yconf_reloaded.to_dict())) > len(sample_dict)  # YConf contains 2 more private keys!

        # remove last cfg file
        saved_cfgs[0].unlink()

        with pytest.raises(OSError):
            yconf = XConfig(output_cfg_filename)

    @pytest.mark.parametrize("cfg_extension", ['yaml', 'json', 'toml'])
    @pytest.mark.parametrize("data", data_to_test())
    def test_creation_root_replace(self, generic_temp_folder, data, cfg_extension):
        """ Test with double @@ -> replace value with content of content
        """
        generic_temp_folder = Path(generic_temp_folder)

        sample_dict, _, _, to_be_raplaced_keys = data
        volatile_dict = copy.deepcopy(sample_dict)

        subtitutions_values = {}
        for k in to_be_raplaced_keys:
            random_name = k + f".{cfg_extension}{XConfig.REFERENCE_QUALIFIER}{XConfig.REFERENCE_QUALIFIER}"
            subtitutions_values[random_name] = pydash.get(volatile_dict, k)

            subtitutions_values[random_name]
            pydash.set_(volatile_dict, k, random_name)

        output_cfg_filename = generic_temp_folder / f'out_config.{cfg_extension}'

        subtitutions_values[str(output_cfg_filename)] = volatile_dict

        saved_cfgs = []
        for output_filename, d in subtitutions_values.items():
            output_filename = generic_temp_folder / output_filename.replace(f'{XConfig.REFERENCE_QUALIFIER}', '')
            store_cfg(output_filename, d)
            saved_cfgs.append(output_filename)

        yconf = XConfig(output_cfg_filename)

        assert DeepDiff(yconf.to_dict(), sample_dict)


class TestXConfigReplace(object):

    @pytest.mark.parametrize("data", data_to_test())
    def test_replace(self, generic_temp_folder, data):

        sample_dict, _, placeholders, _ = data

        conf = XConfig.from_dict(sample_dict)

        np.random.seed(66)

        to_replace = {}
        for p in placeholders:
            to_replace[p] = np.random.randint(0, 10)

        assert len(conf.available_placeholders()) == len(placeholders)

        conf.check_available_placeholders(close_app=False)

        if len(conf.available_placeholders()) > 0:

            for name, p in conf.available_placeholders():
                assert isinstance(name, str)
                assert isinstance(p, XPlaceholder)

            with pytest.raises(SystemExit):
                conf.check_available_placeholders(close_app=True)

            conf.replace_map(to_replace)

            chunks = conf.chunks()
            for key, value in chunks:
                if not isinstance(value, Box) and not isinstance(value, BoxList):
                    assert value not in to_replace.keys()

            assert len(conf.available_placeholders()) == 0


class TestXConfigValidate(object):

    @pytest.mark.parametrize("data", data_to_test())
    def test_validation(self, generic_temp_folder, data):

        sample_dict, schema, _, _ = data

        conf = XConfig.from_dict(sample_dict)
        conf.set_schema(schema)

        print(type(conf.get_schema()))
        conf.validate()
        assert conf.is_valid()

        conf.set_schema(None)
        assert conf.is_valid()

        invalid_schema = Schema({'fake': int})
        conf.set_schema(invalid_schema)
        with pytest.raises(SchemaMissingKeyError):
            conf.validate()
        assert not conf.is_valid()

    # def _test_to_dict(self, generic_temp_folder):
    #     import rich
    #     import npyscreen

    #     def main(self):
    #         F = npyscreen.Form(name="Customize configuration")

    #         placeholders_map = {}
    #         for name, value in conf2.available_placeholders():
    #             # t  = F.add(npyscreen.TitleText, name = "Text:",)
    #             placeholders_map[value] = F.add(npyscreen.TitleText, name=f"{name}:", begin_entry_at=32)
    #         F.edit()
    #         return {name: x.value for name, x in placeholders_map.items()}

    #     sample_dict, schema, _ = self._sample_dict()

    #     output_filename = 'gino.toml'
    #     output_filename = generic_temp_folder / output_filename.replace('@', '')
    #     store_cfg(output_filename, sample_dict)
    #     rich.print(sample_dict)
    #     rich.print(output_filename)

    #     conf2 = XConfig(output_filename)
    #     rich.print(conf2.to_dict())

    #     # conf2.check_available_placeholders()
    #     filled = npyscreen.wrapper_basic(main)
    #     conf2.replace_map(filled)
    #     rich.print(conf2.to_dict())
