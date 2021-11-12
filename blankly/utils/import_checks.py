"""
    Utils file for type & default checking the .JSON imports
    Copyright (C) 2021  Emerson Dove and contributors

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
from typing import Any, Callable, Union, Tuple
from blankly.utils.utils import time_interval_to_seconds
import numpy as np
import re


def is_in_list(val, allowable, case_sensitive: bool = False) -> bool:
    """
    Check if provided value is in the allowable list

    Args:
        val : value to check. Can be of any type
        allowable: list (or single element) to compare the val field to
        case_sensitive: boolean flag for use when comparing strings
    """

    # Force any single element allowable args to be a list
    if not isinstance(allowable, list):
        allowable = [allowable]

    # If the results are not case sensitive, force comparison
    # on lower-case, so the user does not get an error from using caps
    if isinstance(val, str) and not case_sensitive:
        val = val.lower()

    return val in allowable


def is_positive(val) -> bool:
    """
    Check if the provided argument is real and positive
    """
    return np.isreal(val) and val >= 0


def is_timeframe(val: Union[str, int]) -> bool:
    """
    Check if the provided val argument is in the list of allowable args

    Args:
        val : string to evaluate
    """
    try:
        time_interval_to_seconds(val)
        return True
    except ValueError:
        return False


def in_range(val, allowable_range: tuple, inclusive: bool = True) -> bool:
    """
    Check if the provided val is within the specified range

    Args:
        val : int or float to check
        allowable_range : tuple specifying the min and max value
        inclusive : boolean flag to specify if the value can be equal to
            the provide min and max range. Default of True means if the value
            is equal to the min or max, the function returns True
    """
    max_val = max(allowable_range)
    min_val = min(allowable_range)

    if not np.isreal(val):
        return False

    if inclusive:
        does_pass = min_val <= val <= max_val
    else:
        does_pass = min_val < val < max_val

    return does_pass


def are_valid_elements(vals: list, element_constraint: Callable, constraint_args=None) -> bool:
    """
    Check if the elements of a list conform to the provided constraint

    Args:
        vals : list of values to iterate through and check
        element_constraint : function reference used to check each element of the list
        constraint_args : dictionary of keyword arguments to pass to the element 
            constraint function. Default to empty dict.
    """
    if constraint_args is None:
        constraint_args = {}
    does_pass = isinstance(vals, list)
    for val in vals:
        does_pass &= element_constraint(val, **constraint_args)

    return does_pass


def is_valid_email(val):
    """
    Check if the provided argument is a valid email address
    """
    # Regular Expression source https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
    reg_ex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    return re.fullmatch(reg_ex, val)


class UserInputParser:

    def __init__(self, default_val, allowable_types: Union[type, Tuple[type]], logic_check: Callable = None,
                 logic_check_args=None):
        """
        Create a new User Input Checker to ensure inputs from the user are valid.

        Args:
            default_val : If there is an error with the user's input, this is the value the field will default to
            allowable_types: type, or tuple of types that the input argument can be
            logic_check : function reference that will be used to validate the user's input
            logic_check_args : dictionary of arguments to be passed to the logic_check function. Dictionary
                keys must match logic_check function keyword arguments.
        """
        if logic_check_args is None:
            logic_check_args = {}
        self.__default_arg = default_val
        self.__allowable_types = allowable_types
        self.__check_callback: Callable = logic_check
        self.__callback_args: dict = logic_check_args
        self.__warning_str: str = ""
        self.__user_arg = None
        self.__valid: bool = False

    @property
    def default(self):
        """
        Get the default argument provided by the user
        """
        return self.__default_arg

    @property
    def valid(self) -> bool:
        """
        Get the boolean flag indicating if the user's input was valid.
        Note, this field is None until is_valid() is called
        """
        return self.__valid

    @property
    def user_arg(self):
        """
        Get the original argument provided by the user
        """
        return self.__user_arg

    @property
    def warning_str(self) -> str:
        """
        Get the warning string that is constructed when a user's input is invalid
        """
        return self.__warning_str

    def validate_type(self, user_arg: Union[Any, list]) -> bool:
        """
        Take the provided user_arg and compare it to the list of allowable types
        """

        # Check each element of a list
        if isinstance(user_arg, list):
            does_pass = are_valid_elements(user_arg, isinstance, {"__class_or_tuple": self.__allowable_types})
        else:
            does_pass = isinstance(user_arg, self.__allowable_types)

        return does_pass

    def is_valid(self, user_arg) -> bool:
        """
        Take the provided user_arg and run it through the logic_check function
        """

        # Save the provided user arg in case it is needed for error messages
        self.__user_arg = user_arg

        # Compare the user_arg with the list of acceptable types
        # If no check callback is provided, the type verification
        # is sufficient
        if self.validate_type(user_arg) is False:
            warning_string = [f"Provided value of \'{user_arg}\' is of type \'{type(user_arg)}\'. \n"]
            warning_string += ["\t" * 3 + f"Value for this field must be one of the following types: \n"]
            warning_string += ["\t" * 5 + f"- {t} \n" for t in self.__allowable_types] if \
                isinstance(self.__allowable_types, list) else \
                ["\t" * 5 + f"- {self.__allowable_types} \n"]

            self.__warning_str = "".join(warning_string)
            self.__valid = False
            raise TypeError(self.__warning_str)

        elif self.__check_callback is not None:
            self.__valid = self.__check_callback(user_arg, **self.__callback_args)

            if self.__valid is False:
                # Create the warning
                warning_string = [
                    f"Provided value of \'{user_arg}\' did not meet the constraints enforced by: "
                    f"{self.__check_callback.__name__}(). \n"]

                if self.__callback_args is not None:
                    warning_string += ["\t" * 3 + "Arguments passed to constraint function: \n"]
                    warning_string += ["\t" * 5 + f"- {k} : {v.__name__ if isinstance(v, Callable) else v} \n" for k, v
                                       in self.__callback_args.items()]

                # Join the lists of messages together and assign
                self.__warning_str = "".join(warning_string)
                raise ValueError(self.__warning_str)

        # We only get here if everything is okay
        return True
