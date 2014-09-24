
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


import os as _os
import sys as _sys
import socket as _socket

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

class Host(object):
    ''' Object class for getting and setting details on a gridengine host/client '''
            
    def __init__(self,h_ip=""):        
        
        #TODO: check the h_ip is a valid ip or hostname, for now assume it's a hostname
        
        self.hostname = h_ip
        self.ip = '10.40.50.1'
        self.enabled = False
        self.queues = {}
        self.jobs = {}
        #self.setStats(h_ip)
        
    def getJobs(self):
        ''' Return a list of Jobs that are running on this host '''
        
        job_list = []
        
        
        
        
        return job_list
    
    def setStats(self,host_ip=None):
        ''' given a hostname or ip address populate the attributes of this host object '''
        
        # check host exists
        if not host_ip:
            host_ip=self.hostname
        
        connection = True
        
        try:
            self.ip = _socket.gethostbyname(host_ip)
        except _socket.gaierror, msg:
            connection = False            
        
        self.alive = connection
        
        # We need an xml parser to clean this up a bit, we don't need to repeat all this code in each Class
        
        cmd=['qhost','-cb','-q','-j','-h',host_ip,'-xml']
        qstat_bin=_Popen(cmd,stdout=_PIPE,stderr=_PIPE) 
        xml_out,xml_err=qstat_bin.communicate()
        
        if len(xml_err):
            return "Error in querying qhost:",xml_err
        
        xml_root=_fromstring(xml_out)
                
        if xml_root.tag == 'qhost' and len(xml_root.getchildren()) >= 2 :
            this_host_info=xml_root.getchildren()[1]

            self.hostname=this_host_info.attrib['name']
            
            attributes=this_host_info.getchildren()
            
            queue_info = {}
            job_info = {}
            
            for attr in attributes:
                # Queue info            
                if attr.tag == 'queue':
                    queue_info[attr.attrib['name']] = {}
                    
                    for queue_st in attr.getchildren():
                        queue_info[attr.attrib['name']][queue_st.attrib['name']] = queue_st.text
                                    
                    self.queues = queue_info
                    
                elif attr.tag == 'job':
                    job_info[str(attr.attrib['name'])] = {}
                    
                    for job_st in attr.getchildren():
                        try:
                            job_info[str(attr.attrib['name'])][job_st.attrib['name']] = job_st.text
                        except KeyError,msg:
                            print 'Job KEY ERROR when gathering host jobs:',msg        
                    self.jobs = job_info
                                        
                else:
                    setattr(self,attr.attrib['name'],attr.text)
                
    def __repr__(self):
        return 'Host( "%s" )'%str(self)

    def __str__(self):
        return self.hostname

        
        
    
    
        