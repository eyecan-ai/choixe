
from choixe.configurations import XConfig
import rich
from schema import Schema, Use

cfg = {
    'one': {
        's0': '1',
        's1': '22.2',
        's2': 'True'
    },
    'nested': {
        'alphabet': {
            'zero': '0',
            'one': '1'
        }
    }
}

conf = XConfig.from_dict(cfg)
rich.print(conf)


schema = Schema({
    'one': {
        's0': Use(int),
        's1': Use(float),
        's2': Use(bool),
    },
    'nested': {
        'alphabet': {
            'zero': Use(int),
            'one': Use(float)
        }
    }
})
conf.set_schema(schema)
conf.validate()

rich.print(conf)
