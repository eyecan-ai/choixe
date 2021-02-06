from choixe.directives import DirectiveAT
from choixe.placeholders import Placeholder
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
from choixe.configurations import XConfig


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


def generate_placeholder(name: str, tp: str = None):
    if tp is not None:
        if len(tp) > 0:
            return DirectiveAT.generate_directive_string(tp, [name])
    return DirectiveAT.generate_directive_string('str', [name])


def complex_data():
    np.random.seed(666)

    placeholders = [
        generate_placeholder('v_0', 'int'),
        generate_placeholder('v_1', 'float'),
        generate_placeholder('v_2', 'str'),
        generate_placeholder('v_3', 'bool'),
        generate_placeholder('v_4'),
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
            '3.1': 'TrueValue',
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
                '3.1': str,
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
        Box(XConfig.decode(data.to_dict())).to_yaml(filename)
    if 'json' in filename:
        Box(XConfig.decode(data.to_dict())).to_json(filename)
    if 'toml' in filename:
        Box(XConfig.decode(data.to_dict())).to_toml(filename)


class TestXConfig(object):

    @pytest.mark.parametrize("cfg_extension", ['yaml', 'json', 'toml'])
    @pytest.mark.parametrize("data", data_to_test())
    def test_creation(self, generic_temp_folder, data, cfg_extension):  # TODO: toml 0.10.2 needed! toml has a bug otherwise

        generic_temp_folder = Path(generic_temp_folder)

        sample_dict, _, _, to_be_raplaced_keys = data
        volatile_dict = copy.deepcopy(sample_dict)

        subtitutions_values = {}
        for k in to_be_raplaced_keys:
            random_name = k + f".{cfg_extension}"  # {XConfig.REFERENCE_QUALIFIER}"
            random_name = DirectiveAT.generate_directive_string('import', [random_name])
            subtitutions_values[random_name] = pydash.get(volatile_dict, k)

            pydash.set_(volatile_dict, k, random_name)

        output_cfg_filename = generic_temp_folder / f'out_config.{cfg_extension}'
        output_cfg_filename2 = generic_temp_folder / f'out_config2.{cfg_extension}'

        subtitutions_values[str(output_cfg_filename)] = volatile_dict

        saved_cfgs = []
        for directive_value, d in subtitutions_values.items():
            directive = DirectiveAT(value=directive_value)
            if directive.valid:
                output_filename = generic_temp_folder / directive.args[0]
            else:
                output_filename = generic_temp_folder / directive_value
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
            random_name = k + f".{cfg_extension}"  # {XConfig.REFERENCE_QUALIFIER}"
            random_name = DirectiveAT.generate_directive_string('import_root', [random_name])
            # random_name = k + f".{cfg_extension}{XConfig.REFERENCE_QUALIFIER}{XConfig.REFERENCE_QUALIFIER}"
            subtitutions_values[random_name] = pydash.get(volatile_dict, k)

            pydash.set_(volatile_dict, k, random_name)

        output_cfg_filename = generic_temp_folder / f'out_config.{cfg_extension}'

        subtitutions_values[str(output_cfg_filename)] = volatile_dict

        saved_cfgs = []
        for directive_value, d in subtitutions_values.items():
            directive = DirectiveAT(value=directive_value)
            if directive.valid:
                output_filename = generic_temp_folder / directive.args[0]
            else:
                output_filename = generic_temp_folder / directive_value
            # output_filename = generic_temp_folder / output_filename.replace(f'{XConfig.REFERENCE_QUALIFIER}', '')
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
            _p = Placeholder.from_string(p)
            to_replace[_p.name] = np.random.randint(0, 10)

        assert len(conf.available_placeholders()) == len(placeholders)

        conf.check_available_placeholders(close_app=False)

        if len(conf.available_placeholders()) > 0:

            for name, p in conf.available_placeholders().items():
                assert isinstance(name, str)
                assert isinstance(p, Placeholder)

            with pytest.raises(SystemExit):
                conf.check_available_placeholders(close_app=True)

            conf.replace_variables_map(to_replace)

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
