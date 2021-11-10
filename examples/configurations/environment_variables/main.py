from choixe.configurations import XConfig
import rich

##################################
# SETs ENVIRONMENT VARIABLE FIRST
# to pass XConfig check
#
# > export V0=0.0
# > export V1=2.0
# > export V2=3.0
#
##################################

cfg = XConfig(filename="cfg.yml")
cfg.check_available_placeholders(close_app=True)
rich.print(cfg.to_dict())
