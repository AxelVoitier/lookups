# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports

# Third-party imports

# Local imports


class TestParentObject:

    def __str__(self):
        return 'This is ' + self.__class__.__name__


class TestChildObject(TestParentObject):
    pass


class TestOtherObject:

    def __str__(self):
        return 'This is ' + self.__class__.__name__
