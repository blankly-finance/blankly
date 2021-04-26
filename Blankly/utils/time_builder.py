"""
    Time building utils function for easy second building
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


def build_second():
    return 1


def build_minute():
    return build_second() * 60


def build_hour():
    return build_minute() * 60


def build_day():
    return build_hour() * 24


def build_week():
    return build_day() * 7


def build_month():
    return build_day() * 30


def build_year():
    return build_day() * 365


def build_decade():
    return build_year() * 10


def build_century():
    return build_decade() * 10


def build_millennium():
    return build_century() * 10
