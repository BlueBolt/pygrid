
#    (c)2011 Bluebolt Ltd.  All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are
#    met:
#    * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#    * Neither the name of Bluebolt nor the names of
#    its contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#    
#    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#    A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#    OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    Author:Ashley Retallack - ashley-r@blue-bolt.com
#    Created:2011-06-07


''' Main gridengine class '''


from version import *
from Exceptions import *


def getRoot():
	import os
	if 'SGE_ROOT' in os.environ.keys():

		if os.path.isdir(os.environ['SGE_ROOT']):
			_SGE_ROOT=os.environ['SGE_ROOT']
			# detect if  this directory has bin/qstat in it
			arch_bin = _SGE_ROOT+'/util/arch'
			if os.path.isfile(arch_bin):
				return _SGE_ROOT
			else:
				raise GridError('Invalid SGE_ROOT path given, please check your grid engine installation')
		return 
	else:
		raise GridError('No Grid Enigine Root can be found, plase make sure the environment SGE_ROOT has been set')

SGE_ROOT=getRoot()

def mkfolder(path):
	import os as _os
	import errno as _errno
	# create path with folders
	try:
		_os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == _errno.EEXIST: #if folder already exists just pass
			pass
		else: raise

# Now import the sub-modules and classes ..

from Job import * 
from Task import *
from Host import * 
from Queue import * 
from Render import *
from Utils import *
from User import *
from Database import *
from config_gridengine import *
from sql_gridengine import *

# __all__ = ['Job','Task','Host','Queue','Render','Utils']

