#!/usr/bin/env python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Jonathan Foucher <jfoucher@gmail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

###################### DO NOT TOUCH THIS (HEAD TO THE SECOND PART) ######################

from distutils.core import setup
from DistUtilsExtra.command import *
from glob import glob

setup(name="indicator-skype",
      version="0.1",
      author="Jonathan Foucher",
      author_email="jfoucher@gmail.com",
      url="https://github.com/jfoucher/ubuntu-skype-indicator",
      license="GNU General Public License (GPL)",
      scripts=['skype-indicator.py'],
      cmdclass = { "build" :  build_extra.build_extra }
)
