# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports

# Third-party imports
from typing_extensions import override

# Local imports


class TestParentObject:
    @override
    def __str__(self) -> str:
        return 'This is ' + self.__class__.__name__


class TestChildObject(TestParentObject):
    pass


class TestOtherObject:
    @override
    def __str__(self) -> str:
        return 'This is ' + self.__class__.__name__
