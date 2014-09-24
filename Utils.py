
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
#    Version:0.9.82


import os as _os
import sys as _sys

import shutil

import logging

from subprocess import Popen,PIPE

class Colors(object):
    '''defines basic color scheme'''
    OFF = chr(27) + '[0m'
    RED = chr(27) + '[31m'
    GREEN = chr(27) + '[32m'
    YELLOW = chr(27) + '[93m'
    MAGENTA = chr(27) + '[35m'
    CYAN = chr(27) + '[36m'
    WHITE = chr(27) + '[37m'
    BLUE = chr(27) + '[34m'
    BOLD = chr(27) + '[1m'
    COLORS = [OFF, RED, GREEN, YELLOW, MAGENTA, CYAN, WHITE, BLUE, BOLD]


def error(msg):
    ''' print a message in red with "ERROR" at the beginnning '''
        
    print "%sERROR : %s%s" % (Colors.RED,msg,Colors.OFF)

def getQueueList():
    """ Return a list of Queue Objects """
    
    from Queue import Queue
    
    q_list_bin=Popen(['qconf','-sql'],stdout=PIPE)
    
    out,err=q_list_bin.communicate()
    
    queue_list=[]
    
    if not err:
        for q in out.split('\n'):
            if q.endswith('.q'):
                queue_list.append(Queue(q.strip()))
            
        return queue_list
    else:
        error(err)
        return None 
    
def getUserList():
    """ Return a list of User Objects based on pwd entries """
    
    from User import User

    # get own user
    import getpass
    current_user = getpass.getuser()

    queue_hosts_bin=Popen(['qconf','-suserl'],stdout=PIPE)
    out,err=queue_hosts_bin.communicate()

    if not err:
        u_list=[]
        user_in_list = False
        for u in out.split('\n'): 
            try:
                if u == current_user:
                    user_in_list=True
                this_user = User(u)
                u_list.append(User(u))
            except:
                continue

        if not user_in_list:
            u_list.append(User(current_user))

        return sorted(u_list)
    else:
        error(err)
        return None
    

def getHostList(queue='all.q'):
    """ Return the host that are in the chosen 'queue' """    
    from Host import Host
    
    queue_hosts_bin=Popen(['qconf','-sq',queue],stdout=PIPE)
    out,err=queue_hosts_bin.communicate()
    
    hostlist=[]
    
    if not err:
    
        queue_hostlist=''
        
        host_list_str = [] # a simple string list of the hosts before they are objects
        
        for o in out.split('\n'):
            if 'hostlist' in o:
                queue_hostlist=o.split()[1:]
        
        for hg in queue_hostlist:
            if hg.startswith('@'): # hostgroup
            
                hg_hosts_bin=Popen(['qconf','-shgrp',hg],stdout=PIPE)
                
                out,err=hg_hosts_bin.communicate()
                
                if not err:
                    hg_hosts_str_list=out.split()
                    
                    for l in hg_hosts_str_list:
                        if 'blue-bolt.local' in l and l not in host_list_str:
                            host_list_str.append(l)
                            hostlist.append(Host(l))
                else:
                    error(err)
                    break
            
            elif hg.startswith(queue): # individual host
                
                this_host = hg.strip('%s@'%queue)
                
                if this_host not in host_list_str:
                
                    hostlist.append(Host(this_host))
                
        return hostlist

    else:
        error(err)
        return None

def sgeOutputFilter(fp):
    """
    SGE's 'qconf' command has a line-continuation format which we will want to
    parse.  To accomplish this, we use this filter on the output file stream.

    You should "scrub" SGE output like this::

        fp = runCommand(<pbs command>)
        for line in pbsOutputFilter(fp):
           ... parse line ...

    Or simply,

       for line in sgeCommand(<pbs command>):
           ... parse line ...
    """
    class SGEIter:
        """
        An iterator for the SGE output.
        """

        def __init__(self, fp):
            self.fp = fp
            self.fp_iter = fp.__iter__()
            self.prevline = ''
            self.done = False

        def next(self):
            """
            Return the next full line of output for the iterator.
            """
            try:
                line = self.fp_iter.next()
                if not line.endswith('\\'):
                    result = self.prevline + line
                    self.prevline = ''
                    return result
                line = line.strip()[:-1]
                self.prevline = self.prevline + line
                return self.next()
            except StopIteration:
                if self.prevline:
                    results = self.prevline
                    self.prevline = ''
                    return results
                raise

    class SGEFilter:
        """
        An iterable object based upon the SGEIter iterator.
        """

        def __init__(self, myiter):
            self.iter = myiter

        def __iter__(self):
            return self.iter

    return SGEFilter(SGEIter(fp))



def runCommand(cmd):
    ''' little wrapper for running comands as subprocesses and catching errors '''
        
    exe = Popen(cmd.split(), stdout=PIPE,stderr=PIPE)
    
    stdout,stderr = exe.communicate()
    
    exitStatus = exe.wait()
    
    if exitStatus:
        log = getLogger()
        log.info('Command %s exited with %d, stderr: %s' % (cmd, _os.WEXITSTATUS(exitStatus), stderr))

    return stdout
       
def getLogger(name=None):
    """
    Returns a logger object corresponding to `name`.
    
    @param name: Name of the logger object.
    """
    
    return logging.getLogger(name)

def copyFile(src,des):
    ''' simple copy function to copy a given source file to a destination '''
    
    try:
        shutil.copy2(src, des)
    except Exception,e:
        raise Exception(e)

    if _os.path.isdir(des):
        return _os.path.join(des,_os.path.basename(src))
    elif _os.path.isfile(des):
        return des
    else:
        return None

