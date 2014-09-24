#******************************************************************************
# (c)2011 BlueBolt Ltd.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
# * Neither the name of BlueBolt nor the names of
# its contributors may be used to endorse or promote products derived
# from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# Author:Ashley Retallack - ashley-r@blue-bolt.com
# 
# File:Exceptions.py
# 
# 
#******************************************************************************


class WorkspaceError(Exception):
    ''' Custom exception for catching workspace errors '''
    def __init__(self,value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class QueueError(Exception):
    ''' Custom exception for catching Queue errors '''
    def __init__(self,value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class HostError(Exception):
    ''' Custom exception for catching Host errors '''
    def __init__(self,value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class JobError(Exception):
    ''' Custom exception for catching Job errors '''
    def __init__(self,value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class UserError(Exception):
    ''' Custom exception for catching User class errors '''
    def __init__(self,value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class NoFileError(Exception):
    ''' Custom exception when there is no file present or intended to be generated'''
    def __init__(self,value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class GridError(Exception):
    ''' Custom Exception for catching generic grid errors '''
    def __init__(self,value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)
    
    
