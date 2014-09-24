
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
#    Version:

import pwd

class User(object):

    def __init__(self,username):

        pwd_data = pwd.getpwnam(username)
        self.username = username
        self.email = '%s@blue-bolt.com'%username
        self.fullname = pwd_data.pw_gecos
        self.uid = pwd_data.pw_uid
        self.gid = pwd_data.pw_gid
        self.shell = pwd_data.pw_shell

        self._project = None

    def isAdmin(self):
        pass

    def isOperator(self):
        pass

    def project():
        doc = "The foo property."
        def fget(self):            

            # do drmaa / qmod stuff

            return self._project
        def fset(self, value):
            o_value = value
            if not isinstance(list,o_value):
                o_value = [value]

            # do drmaa / qmod stuff

            self._project = o_value
        def fdel(self):
            del self._project
        return locals()

    project = property(**project())

    def __repr__(self):
        return 'User( "%s" )'%str(self)

    def __str__(self):
        return self.username
