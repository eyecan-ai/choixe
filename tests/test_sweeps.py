import pytest
from choixe.importers import Importer
from choixe.configurations import XConfig
from choixe.placeholders import Placeholder


class TestSweeps:
    def _build_sweep(self, values):
        return f"@sweep({','.join(map(str,values))})"

    def test_sweeps(self):

        ints = [1, 2, 3]
        floats = [1.0, 2.0, 3.0]
        strings = ['"a"', '"b"', '"c"']
        bools = [True, False]

        root_cfg = {
            "first_level": 1,
            "second": {
                "ints": self._build_sweep(ints),
                "floats": self._build_sweep(floats),
                "strings": self._build_sweep(strings),
                "bools": self._build_sweep(bools),
            },
        }

        cfg = XConfig.from_dict(root_cfg)
        assert len(cfg.available_placeholders()) == 4
        sweeped_cfgs = cfg.sweep()

        total = len(ints) * len(floats) * len(strings) * len(bools)
        assert len(sweeped_cfgs) == total

    def test_nosweeps(self):

        root_cfg = {
            "first_level": 1,
            "second": {
                "alpha": [1, 2, 3],
            },
        }
        cfg = XConfig.from_dict(root_cfg)
        assert len(cfg.sweep()) == 1
