from dynaconf import Dynaconf

from dicty.utils import get_path_relative_to_script


settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=[get_path_relative_to_script(f) for f in ['settings.yaml', '.secrets.yaml']],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
