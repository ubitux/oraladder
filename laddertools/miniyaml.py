#
# Copyright (C) 2020
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re


_LINE_RE = re.compile(r'^(?P<indent>\t*)(?:(?P<key>[^:]*):\s*)?(?P<value>.*)')


def _cleanup(d):
    if d == {}:
        return ''
    for k, v in d.items():
        if not isinstance(v, dict):
            continue
        d[k] = _cleanup(d[k])
    return d


def load(yaml_str):
    yaml_str = yaml_str.decode()
    levels = [{}]
    for line in yaml_str.splitlines():
        m = re.match(_LINE_RE, line)
        indent, key, value = m.group('indent', 'key', 'value')
        level = len(indent)
        if not key:
            continue
        if not value:
            value = {}
            levels = levels[:level + 1] + [value]
        parent = levels[level]
        parent[key] = value
    return _cleanup(levels[0])
