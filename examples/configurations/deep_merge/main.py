from choixe.configurations import XConfig
import rich

conf = XConfig(filename='cfg.yml')
conf_to_replace = XConfig(filename='cfg_deep.yml')

rich.print(conf.to_dict())
rich.print(conf_to_replace.to_dict())

# Deep Update
conf.deep_update(conf_to_replace)
rich.print(conf.to_dict())
