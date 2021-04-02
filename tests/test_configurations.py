import os
from choixe.directives import DirectiveAT
from choixe.placeholders import Placeholder
from typing import Sequence, Union
import copy
from box.box_list import BoxList
import numpy as np
from box.box import Box
from deepdiff import DeepDiff
from schema import Schema, Or, Regex, SchemaMissingKeyError, Use

import pydash
from pathlib import Path
import pytest
from choixe.configurations import XConfig


@pytest.fixture(scope="function")
def generic_temp_folder(tmpdir_factory):
    fn = tmpdir_factory.mktemp("_choixe_temp_folder")
    return fn


class PlaceholderGenerator:
    def __init__(self, base_name: str = 'v_') -> None:
        self.counter = 0
        self.base_name = base_name

    def create_placeholder(self, collection: Sequence, tp: str = None, others: Sequence = None):
        args = [f'{self.base_name}{self.counter}']
        if others is not None:
            args.extend(others)
        if tp is not None:
            if len(tp) > 0:
                p = DirectiveAT.generate_directive_string(tp, args)
                collection.append(p)
                return p

        # Default type
        p = DirectiveAT.generate_directive_string('str', args)
        collection.append(p)
        return p


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

    return {
        'data': sample_dict,
        'schema': schema,
        'placeholders': [],
        'environment_variables': [],
        'to_be_replaced': to_be_raplaced_keys
    }


def complex_data():
    np.random.seed(666)

    placeholders = []
    env_variables = []
    pl_generator = PlaceholderGenerator()

    sample_dict = {
        'one': pl_generator.create_placeholder(placeholders, 'int', [6, 7, 8, 'default=10']),
        'two': np.random.randint(-50, 50, (3, 3)).tolist(),
        'three': {
            '3.1': 'TrueValue',
            '2.1': [False, False],
            'name': {
                'name_1': pl_generator.create_placeholder(placeholders, 'float'),
                'name_2': 2,
                'name_3': {
                    'this_is_a_list': [3.3, 3.3],
                    'this_is_A_dict': {
                        'a': {
                            'f': True,
                            's': False,
                            'numpy_array': np.array([1., 2, 3]),
                            'numpy_data': np.array([1., 2, 3])[0],
                            'tuple': ('a', 'b', '2'),
                            'boxlist': BoxList([1, 2, 3, 4]),
                            'boxdict': Box({'a': 2.2})
                        }
                    }
                }
            }
        },
        'first': {
            'f1': pl_generator.create_placeholder(placeholders, 'str', ['alpha', 'beta', 'gamma']),  # placeholders[2],
            'f2': 2.22,
            'f3': [3, 3, 3, 3, 3, 3],
            'external': {
                'ext': np.random.uniform(-2, 2, (2, 3)).tolist(),
                'ext_name': [pl_generator.create_placeholder(placeholders, 'bool')],
            },
            'ops': {
                'o1': pl_generator.create_placeholder(placeholders),  # placeholders[4],
                'o2': pl_generator.create_placeholder(placeholders, 'path'),  # placeholders[5],
                'o3': pl_generator.create_placeholder(placeholders, 'date'),  # placeholders[6],
                'o4': pl_generator.create_placeholder(placeholders, 'str', ['A', 'B', 'C', 'default=C']),  # placeholders[7],
                'o5': pl_generator.create_placeholder(placeholders),  # placeholders[8],
                'o6': pl_generator.create_placeholder(placeholders),  # placeholders[9]
            },
            'env': [
                pl_generator.create_placeholder(placeholders, 'env'),  # env_variables[0],
                pl_generator.create_placeholder(placeholders, 'env')
            ],
            'key': {
                'with': 120,
                'dots': pl_generator.create_placeholder(placeholders, 'object'),
            },
            'key.with.dots': pl_generator.create_placeholder(placeholders),  # placeholders[10],
            'key.with...many.....dots': pl_generator.create_placeholder(placeholders),
            'nested.key': {
                'with.dots': pl_generator.create_placeholder(placeholders)
            },
            'placeholder_object': pl_generator.create_placeholder(placeholders),
            'placeholder_cfg': pl_generator.create_placeholder(placeholders, 'cfg'),  # placeholders[15],
            'placeholder_cfg_root': pl_generator.create_placeholder(placeholders, 'cfg_root'),  # ,
        }
    }

    schema = Schema(
        {
            'one': Or(int, str),
            'two': list,
            'three': {
                '3.1': str,
                '2.1': [bool],
                'name': dict,
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

    return {
        'data': XConfig.decode(sample_dict),
        'schema': schema,
        'placeholders': placeholders,
        'environment_variables': env_variables,
        'to_be_replaced': to_be_raplaced_keys
    }


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


TESTABLE_ESTENSIONS = ['yaml', 'json', 'toml']


class TestXConfig(object):

    @pytest.mark.parametrize("cfg_extension", TESTABLE_ESTENSIONS)
    @pytest.mark.parametrize("data", data_to_test())
    def test_creation(self, generic_temp_folder, data, cfg_extension):  # TODO: toml 0.10.2 needed! toml has a bug otherwise

        generic_temp_folder = Path(generic_temp_folder)

        sample_dict = data['data']
        to_be_raplaced_keys = data['to_be_replaced']  # , _, _, to_be_raplaced_keys = data
        volatile_dict = copy.deepcopy(sample_dict)

        subtitutions_values = {}
        for k in to_be_raplaced_keys:
            random_name = k + f".{cfg_extension}"
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

        with pytest.raises(NotImplementedError):
            yconf.save_to(str(output_cfg_filename2) + "#IMPOSSIBLE.EXTENSION")

        assert not DeepDiff(yconf.to_dict(), sample_dict)
        assert not DeepDiff(yconf_reloaded.to_dict(), sample_dict)
        assert not DeepDiff(XConfig.from_dict(yconf_reloaded.to_dict()).to_dict(), yconf_reloaded.to_dict())
        assert len(XConfig.from_dict(yconf_reloaded.to_dict())) > len(sample_dict)  # YConf contains 2 more private keys!

        # remove last cfg file
        saved_cfgs[0].unlink()

        with pytest.raises(OSError):
            yconf = XConfig(output_cfg_filename)

    @pytest.mark.parametrize("cfg_extension", TESTABLE_ESTENSIONS)
    @pytest.mark.parametrize("data", data_to_test())
    def test_creation_root_replace(self, generic_temp_folder, data, cfg_extension):
        """ Test with double @@ -> replace value with content of content
        """
        generic_temp_folder = Path(generic_temp_folder)

        sample_dict = data['data']
        to_be_raplaced_keys = data['to_be_replaced']  # , _, _, to_be_raplaced_keys = data
        volatile_dict = copy.deepcopy(sample_dict)

        subtitutions_values = {}
        for k in to_be_raplaced_keys:
            random_name = k + f".{cfg_extension}"
            random_name = DirectiveAT.generate_directive_string('import_root', [random_name])
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
            store_cfg(output_filename, d)
            saved_cfgs.append(output_filename)

        yconf = XConfig(output_cfg_filename)

        assert DeepDiff(yconf.to_dict(), sample_dict)


class TestXConfigReplace(object):

    @pytest.mark.parametrize("data", data_to_test())
    def test_replace(self, generic_temp_folder, data):

        sample_dict = data['data']
        placeholders = data['placeholders']  # , _, _, to_be_raplaced_keys = data
        environment_variables = data['environment_variables']

        conf = XConfig.from_dict(sample_dict)

        np.random.seed(66)

        to_replace = {}
        for p in placeholders:
            _p = Placeholder.from_string(p)
            to_replace[_p.name] = np.random.randint(0, 10)

        assert len(conf.available_placeholders()) == len(placeholders) + len(environment_variables)

        conf.check_available_placeholders(close_app=False)

        if len(conf.available_placeholders()) > 0:

            for name, p in conf.available_placeholders().items():
                assert isinstance(name, str)
                assert isinstance(p, Placeholder)

            with pytest.raises(SystemExit):
                conf.check_available_placeholders(close_app=True)
            conf.replace_variables_map(to_replace)

            chunks = conf.chunks_as_lists()
            for key, value in chunks:
                if not isinstance(value, Box) and not isinstance(value, BoxList):
                    assert value not in to_replace.keys()

            assert len(conf.available_placeholders()) == len(environment_variables)


class TestXConfigEnvironmentVariable(object):

    @pytest.mark.parametrize("data", data_to_test())
    def test_env_variables(self, generic_temp_folder, data):

        sample_dict = data['data']
        placeholders = data['placeholders']  # , _, _, to_be_raplaced_keys = data
        environment_variables = data['environment_variables']

        conf = XConfig.from_dict(sample_dict)
        np.random.seed(66)

        assert len(conf.available_placeholders()) == len(placeholders) + len(environment_variables)

        for envv in environment_variables:
            pl = Placeholder.from_string(envv)
            assert pl.name not in os.environ, f"this PYTEST needs no environment variable with name '{pl.name}' "

        # Load and parse environment variables but nobody set them!
        conf = XConfig.from_dict(sample_dict, replace_environment_variables=True)
        assert len(conf.available_placeholders()) == len(placeholders) + len(environment_variables)

        # Load and parse environment variables with manual set
        for envv in environment_variables:
            pl = Placeholder.from_string(envv)
            os.environ[pl.name] = str(np.random.uniform(0, 1, (1,)))

        conf = XConfig.from_dict(sample_dict, replace_environment_variables=True)

        import rich
        rich.print(conf)
        assert len(conf.available_placeholders()) == len(placeholders)

        for envv in environment_variables:
            pl = Placeholder.from_string(envv)
            del os.environ[pl.name]


class TestXConfigValidate(object):

    @pytest.mark.parametrize("data", data_to_test())
    def test_validation(self, generic_temp_folder, data):

        sample_dict = data['data']
        schema = data['schema']  # , _, _, to_be_raplaced_keys = data

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


class TestXConfigCopy(object):

    def test_copy(self, sample_configurations_data):

        for config in sample_configurations_data:
            filename = config['filename']
            xcfg = XConfig(filename=filename, no_deep_parse=True)
            print("#"*10)
            print(filename)
            print(xcfg)
            xcfg_copy = xcfg.copy()
            xcfg_copy.deep_parse()
            xcfg_correct = XConfig(filename=filename)
            assert not DeepDiff(xcfg_correct.to_dict(), xcfg_copy.to_dict())
            assert xcfg_copy == xcfg_correct


class TestXConfigChunksView(object):

    def test_chunks_view(self, sample_configurations_data):

        for config in sample_configurations_data:
            filename = config['filename']
            xcfg = XConfig(filename=filename, no_deep_parse=True)

            assert len(xcfg.chunks_as_lists()) > 0
            assert len(xcfg.chunks_as_lists()) == len(xcfg.chunks_as_tuples())
            assert len(xcfg.chunks()) == len(xcfg.chunks_as_tuples())

            ls = xcfg.chunks_as_lists()
            ts = xcfg.chunks_as_tuples()

            for idx in range(len(ls)):
                l, _ = ls[idx]
                t, _ = ts[idx]
                for kidx in range(len(l)):
                    assert l[kidx] == t[kidx]


class TestXConfigDeepSet(object):

    def test_deepset(self):

        cfg = {
            'l1': 'L1',
            'l2': {
                'l2_0': 'L20',
                'l2_1': 'L21',
            },
            'l3': {
                'l3_0': {
                    'l3_0_0': 'L300',
                    'l3_0_1': 'L301',
                    'l3_0_2': 'L302',
                }
            }
        }

        xcfg = XConfig.from_dict(cfg)

        for k, old_value in xcfg.chunks_as_lists():
            row_dict = {}
            pydash.set_(row_dict, k, old_value)

            xrow_dict = XConfig.from_dict(row_dict)
            for newk, newv in xrow_dict.chunks_as_lists():

                # VALID KEYS
                # Try to replace present keys only with ONLY_VALID_KEYS = TRUE, should be equal!
                new_xcfg = xcfg.copy()
                new_xcfg.deep_set(newk, newv, only_valid_keys=True)
                assert not DeepDiff(xcfg.to_dict(), new_xcfg.to_dict())

                # Try to replace present keys only with ONLY_VALID_KEYS = FALSE, should be equal!
                new_xcfg = xcfg.copy()
                new_xcfg.deep_set(newk, newv, only_valid_keys=False)
                assert not DeepDiff(xcfg.to_dict(), new_xcfg.to_dict())

                # INVALID KEYS
                new_keys = ['xxIMPOSSIBLE_KEY'] * 10
                # Try to replace not present keys but ONLY_VALID_KEYS = TRUE, should be equal!
                new_xcfg = xcfg.copy()
                new_xcfg.deep_set(new_keys, newv, only_valid_keys=True)
                assert not DeepDiff(xcfg.to_dict(), new_xcfg.to_dict())

                # Try to replace not present keys but ONLY_VALID_KEYS = False, should be different!
                new_xcfg = xcfg.copy()
                new_xcfg.deep_set(new_keys, newv, only_valid_keys=False)
                assert DeepDiff(xcfg.to_dict(), new_xcfg.to_dict())

    def test_deep_update(self):

        cfg = {
            'l1': 'L1',
            'l2': {
                'l2_0': 'L20',
                'l2_1': 'L21',
            },
            'l3': {
                'l3_0': {
                    'l3_0_0': 'L300',
                    'l3_0_1': 'L301',
                    'l3_0_2': 'L302',
                }
            }
        }

        cfg_to_replace = {
            'l3': {
                'l3_0': {
                    'l3_0_2': 'NEW_L302',
                }
            },
            'not_present_key': {
                'depth': {
                    'alpha': 'alpha'
                }
            }
        }

        xcfg = XConfig.from_dict(cfg)
        xcfg_to_replace = XConfig.from_dict(cfg_to_replace)

        # No Full merge
        new_cfg = xcfg.copy()
        new_cfg.deep_update(xcfg_to_replace, full_merge=False)
        assert len(xcfg.chunks_as_lists()) == len(new_cfg.chunks_as_lists())
        assert DeepDiff(xcfg.to_dict(), new_cfg.to_dict())

        # Full merge
        new_cfg = xcfg.copy()
        new_cfg.deep_update(xcfg_to_replace, full_merge=True)
        assert len(xcfg.chunks_as_lists()) < len(new_cfg.chunks_as_lists())


class TestXConfigValidateWithReplace(object):

    def test_validate_with_replace(self):

        for replace in [True, False]:
            cfg = {
                'one': {
                    's0': '1',
                    's1': '22.2',
                    's2': 'True'
                }
            }

            conf = XConfig.from_dict(cfg)

            schema = Schema({
                'one': {
                    's0': Use(int),
                    's1': Use(float),
                    's2': Use(bool),
                }
            })
            conf.set_schema(schema)
            conf.validate(replace=replace)

            assert isinstance(conf.one.s0, int) == replace
            assert isinstance(conf.one.s1, float) == replace
            assert isinstance(conf.one.s2, bool) == replace
