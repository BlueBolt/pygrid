
#    (c)2012 Bluebolt Ltd.  All rights reserved.
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
#    Version:


class ComplexType(object):

        '''
            Enum for the type of compex, 

            @ INT :- integar
        '''
        INT = 0
        STRING = 1
        TIME = 3
        MEMORY = 4
        BOOL = 5
        CSTRING = 6
        HOST = 7
        DOUBLE = 8
        RESTRING = 9

class Complex(object):
	"""docstring for Complex"""
	def __init__(self, name,default=0):
		super(Complex,name,default).__init__()
		self.name = name
		self.shortcut = ''
		self.type = ComplexType.INT
		self.value = None
		self.relation = '==' # options are '==','>=','>','<','<=','!=','EXCL'
		self.requestable = 'YES' # options are 'YES','NO' or 'FORCED'
		self.consumable = 'NO' # options are 'YES','NO', ot 'JOB'
		self.default = default
		self.urgency = 0

		self._getData()

	def getData(self):
		"""Retreve data from Grid Engine and fill in the attribute of this instance based on the name given"""
		pass

	def create(self):
		"""create this instance in Grid Engine"""
		pass

	def delete(self):
		"""delete this instance from Grid Engine"""
		pass

	def save(self):
		"""save changes to Grid Engine"""
		pass

	def __repr__(self):
		return "Complex(%s)"%self.__str__()

	def __str__(self):
		return self.name

		