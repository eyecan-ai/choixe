import pytest
from choixe.importers import Importer
from choixe.configurations import XConfig
from choixe.placeholders import Placeholder


class TestPlaceholders:

    def test_directiveat_defaults(self):

        items = [
            {
                'values': ['VNAME', 4, 666, 1222],
                'template':'@int({},default={})'
            },
            {
                'values': ['ANAME', 4.1, 666.6, 1.222, 66.6666],
                'template':'@float({},default={})'
            },
            {
                'values': ['SNAME', 'bb', 'ccc'],
                'template':'@str({},default={})'
            }
        ]

        for item in items:
            values = item['values']
            template = item['template']
            for v in values[1:]:
                t = template.format(','.join(map(str, values)), v)
                print("Template, ", t)
                p = Placeholder.from_string(t)
                assert p is not None
                assert p.cast(p.default_value) == v

                assert len(p.options) == len(values) - 1
                print(p.directive._kwargs)


class TestCFGPlaceholders:

    def test_cfg_placeholder(self, sample_configurations_data):

        for sample_cfg in sample_configurations_data:

            fname = sample_cfg["filename"]
            root_cfg = {
                'first_level': 1,
                'second': {
                    'second.1': f'@cfg(TO_IMPORT,{fname})',
                    'second.2': f'@cfg_root(TO_IMPORT_ROOT,{fname})',
                }
            }
            print(root_cfg)

            root_cfg = XConfig.from_dict(root_cfg)
            copy_cfg = root_cfg.copy()

            assert len(root_cfg.available_placeholders()) == 2

            # IMPORT
            for key, placeholder in root_cfg.available_placeholders().items():
                assert placeholder is not None
                assert len(placeholder.options) == 1
                importer_string = placeholder.cast(placeholder.options[0])
                print(importer_string)
                importer = Importer.from_string(importer_string)
                assert importer is not None
                print("REPLACING", key)
                root_cfg.replace_variable(placeholder.name, placeholder.options[0])

            assert len(root_cfg.available_placeholders()) == 0

            print("\nNEW_CFG", root_cfg)
            root_cfg.deep_parse()
            print("\nNEW_CFG", root_cfg)

            new_keys = [x[0] for x in root_cfg.chunks_as_tuples(discard_private_qualifiers=True)]
            old_keys = [x[0] for x in copy_cfg.chunks_as_tuples(discard_private_qualifiers=True)]

            assert len(new_keys) > len(old_keys)
