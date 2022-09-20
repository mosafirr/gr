#    Haruka Aya (A telegram bot project)
#    Copyright (C) 2017-2019 Paul Larsen
#    Copyright (C) 2019-2021 Akito Mizukito (Haruka Aita)

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from haruka import CONFIG, logging


def __list_all_modules():
    """
    Loads modules in the order set
    by the config file, making sure
    to exclude modules that have
    been set not to be loaded
    """

    from os.path import dirname, basename, isfile
    import glob

    # This generates a list of modules in this folder for the * in __main__ to work.
    paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3] for f in paths if isfile(f) and f.endswith(".py")
        and not f.endswith('__init__.py') and not f.endswith('__main__.py')
    ]

    if CONFIG.load or CONFIG.no_load:
        to_load = CONFIG.load
        if to_load:
            if not all(
                    any(mod == module_name for module_name in all_modules)
                    for mod in to_load):
                logging.error("Invalid load order names. Quitting.")
                quit(1)
        else:
            to_load = all_modules

        if CONFIG.no_load:
            logging.info(f"Not loading: {CONFIG.no_load}")
            return list(
                filter(lambda m: m not in CONFIG.no_load,
                       [item for item in to_load]))

        return to_load

    return all_modules


ALL_MODULES = sorted(__list_all_modules())
logging.info("Modules to load: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]
