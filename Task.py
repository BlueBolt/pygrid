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
# File:Task.py
# 
# 
#******************************************************************************

'''

 Task objects are individual members of a submitted Array Job object.
 
 They contain the information on an individualy sub-task of a Grid-Engine Array Job

'''

from Queue import Queue
from User import User
from ParallelEnvironment import ParallelEnvironment

import drmaa as _drmaa

decodestatus = {
    _drmaa.JobState.UNDETERMINED: 'unknown',
    _drmaa.JobState.QUEUED_ACTIVE: 'queued',
    _drmaa.JobState.SYSTEM_ON_HOLD: 'queued',
    _drmaa.JobState.USER_ON_HOLD: 'paused',
    _drmaa.JobState.USER_SYSTEM_ON_HOLD: 'paused',
    _drmaa.JobState.RUNNING: 'running',
    _drmaa.JobState.SYSTEM_SUSPENDED: 'suspended',
    _drmaa.JobState.USER_SUSPENDED: 'suspended',
    _drmaa.JobState.DONE: 'finished',
    _drmaa.JobState.FAILED: 'failed',
}

class Task(object):
    ''' main grid-engine Task type '''
    
    def __init__(self,task_id=0,job=None):
        super(Task, self).__init__()
        self.tid = task_id
        self.job = job # parent Job this task belongs to
        self.label = 'task_label'
        self.name = 'task_name'
        
        # populate the base info based on the job that has been added
        self.wd = ''
        self.command = ''
        self.resources = []
        self.pe = None
        self.queue = Queue('all.q')
    
    def reSubmit(self):
        ''' resubmit this task as a new task'''
        pass
    
    def kill(self):
        ''' force stop this task on all clients'''
        pass 
    
    def stop(self):
        ''' gentle stop this task on all clients, wait for process to return stopped'''
        pass
    
    def pause(self):
        ''' set this job to pause state'''
        pass
    
    def unPause(self):
        '''un pause this task if it is in a user-induced paused state'''
        pass
    
    def setCpus(self):
        ''' set the number of cpus to use for this task'''
        pass
    
    def getResources(self):
        ''' return a list of resources that this job is requesting with total amounts'''
        pass
    
    def getStatus(self):
        ''' get the current status of this task queue '''
        pass
    
    def getWhy(self):
        ''' return any reason why this task is not running '''
        pass

    def getHosts(self):
        ''' return a list of hosts that this task has run on '''

        return []
    
    def __iter__(self):
        return iter(eval(str(self)).items())
    
    def __repr__(self):
        return 'Task( %s )'%(str(self.tid))

    def __str__(self):
        return str(vars(self))

