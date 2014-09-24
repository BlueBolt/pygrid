"""
(c)2011 Bluebolt Ltd.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
* Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following disclaimer
in the documentation and/or other materials provided with the
distribution.
* Neither the name of Bluebolt nor the names of
its contributors may be used to endorse or promote products derived
from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Author:Ashley Retallack - ashley-r@blue-bolt.com
Created:2011-06-07
Version:0.9.2
"""

'''
GRID Engine configuation module

provides interfaces for :
	
	queues
	hosts
	complexes/consumables
	users
	parallel environments
	

'''

import os as _os

import ConfigParser as _CfgParser
import io as _io

#get the config.ini if it exists

	
def get_config():
	pwd = _os.path.dirname(__file__)	
	cfg_fpath =  _os.path.join(pwd,'config.ini') 
	try:
		cfg_file = open(cfg_fpath)
		cfg=cfg_file.read()
		cfg_file.close()
	except IOError as (errno, strerror):
		print "ERROR : no config.ini file found in pygrid base directory (%s)"%(cfg_fpath)
		print "I/O error({0}): {1}".format(errno, strerror)
		
	config = _CfgParser.RawConfigParser()
	config.readfp(_io.BytesIO(cfg))
		
	return config
	
