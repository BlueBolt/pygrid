
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
#    Created:2012-02-17
#    Version:


from Host import Host
from ParallelEnvironment import ParallelEnvironment
import Utils

from subprocess import (
                    Popen as _Popen,
                    PIPE as _PIPE
                    )

from xml.etree.ElementTree import (
                                Element as _Element,
                                ElementTree as _ElementTree,
                                SubElement as _SubElement,
                                parse as _parse,
                                fromstring as _fromstring
                                )


class Queue():    
    """
    Class module for the gridengine 'queue' type
    """
        
    def __init__(self,queue='all.q'):
    
        self.name = str(queue)
        self.enabled = False
        self.jobs = [] # list of jobs running ono this queue
        self.pe_list = [] # list of parallel environments that can be used on this queue
        self.slots = {'self':8} # dictionary of the slots that are set per host on this queue
        self.tmpdir = '/tmp'
        self.shell = '/bin/csh'
        self.prolog = None
        self.epilog = None
        self.shell_start_mode = 'posix_compliant'
        self.starter_method = None
        self.suspend_method = None
        self.resume_method = None
        self.terminate_method = None
        self.notify = 60 # notify time in seconds, before KILL signal is sent after user initiaiated signal
        self.owner_list = {'self':None} # dictionary of owners for the queue / hostgroups / hosts
        self.calander = {'self':None} # dictioary of the calanders that have been applied to the queue / hostgroups / hosts
                        
    def hosts():
        doc = "The hosts property."
        def fget(self):
            self._hosts = Utils.getHostList(self.name)        
            return self._hosts 
        def fset(self, value):
            self._hosts = value
        def fdel(self):
            del self._hosts
        return locals()
    hosts = property(**hosts())
        
    def setStats(self,queue_name):
        ''' Given queue_name set the stats for this queue object '''
        
        # check host exists
        if not queue_name:
            queue_name=self.name                    
        
        # fill in data for this queue
        
        my_dict=dict()
        fp = Utils.runCommand('qconf -sq %s'%queue_name)
        opt = Utils.sgeOutputFilter(fp.split('\n'))
        for line in opt:
            if len(line):
                key=line.split()[0]
                l=line.strip(key)
                l=l.replace(' ', '')
                values=list()
                for v in l.split(','):
                    values.append(v)
                my_dict[key]=values

        self.slots = my_dict['slots']
        # status
        
        # pe_list
               
        
        return True

    
    def disable(self):
        """ Disable all hosts on this queue """
                
        return True
    
    def isDisabled(self):
        """ Return True if all hosts on this queue are disabled"""
        
        return False
    
    def isEnabled(self):
        """ Return True if some hosts on this queue are enabled"""
        
        return True

    
    def getJobs(self):
        """ Return a list of jobs assigned to this queue"""
        
        jobs_list = list()
        
        return jobs_list
    
    def getUsers(self):
        """ Return a list of users with jobs on this queue"""
        
        users_list = list()
        
        return users_list
    
    def getInstances(self):
        """ Return a list of queue instances (host configs)"""
        
        instance_list = list()
        
        return instance_list
    
    def getCalander(self):
        """ Return any calanders assigned to this queue"""
        
        calander = None
        
        return calander
    
    def setCalander(self):
        """ set the calander assigned to this queue"""
    
        return True
    
    def __iter__(self):
        return vars(self)
    
    def __repr__(self):
        return 'Queue( \'%s\' )'%str(self)

    def __str__(self):
        return str(self.name)
