#******************************************************************************
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
#    Version:0.9.2


'''
    Main generic command class

''' 
from gridengine.Job import Job,JobType,mkfolder
from gridengine.Queue import Queue

import os as _os 

class CommandJob(Job):
    ''' default command job instance of gridengine submitting Job class '''
    def __init__(self,jid=None):
        super(CommandJob, self).__init__(jid)
        self.name = 'command_job'
        self.type = JobType.SINGLE
        self.label = 'cmd'
        self.queue = Queue('all.q')        
        self.prescript = "" #: any commands or functions than want to be run at the start of the script        
        self.postscript = "" #: any commands or functions than want to be run at the end of the script
        
        #command args 
        self.cmd='ls -l /'
    
    def setJobName(self):
        '''
            Set the name of the job based on SHOT, daily Version and datetime stamp
        '''
        dt = self.dt.strftime('%Y%m%d%H%M%S')
        self.name='cmd.%s.%s' % (self.cmd.split()[0],dt)
    
        
    def createJobScript(self):
        '''
            Generate the job script for this submission to grid
        '''
        
        envs = ""
        
        for e,v in self.envs.items():
            envs += "export %s=%s;echo %s=${%s};\n" % (e,v,e,e)
        
        settings={'cmd':self.cmd,'envs':envs,'prescript':self.prescript,'postscript':self.postscript,'host_ip':self.submit_host,'host_port':self.portid}

        if not _os.path.isdir(self.paths['scripts_path']):
            mkfolder(self.paths['scripts_path'])
    
        f = open(self.paths['scripts_path']+"/"+self.label + ".%s"%self.dt.strftime('%Y%m%d%H%M%S') +".sh", 'w')
        
        f.write('''#!/bin/bash
#$ -S /bin/bash
#$ -j y
umask 0002

echo "HOST -> $HOSTNAME"
echo "DATE ->" `date`

%(prescript)s

%(envs)s

#Run it
function this_task(){

cmd="%(cmd)s"
echo $cmd

time eval $cmd

exitstatus=$?

if [ $exitstatus != 0 ];then
return 100
fi

return $exitstatus

}

eval this_task

%(postscript)s

# TODO: try and send signal to original host that task was complete



''' % (settings))
    
    
        f.close()

        self.scripts['cmd_script'] = {'script':f.name,'type':1,'name':'cmd'}
        
        self.script = f.name
        
        return f
        
    
    def setWD(self,directory):
        ''' Set the working directory for this job, this is where the log output will be put'''
        
        self.wd=_os.path.abspath(directory)
        self.paths['log_path']='%s/log' % self.wd    
        self.paths['scripts_path']='%s/scripts' % self.wd    
        
        

    def createQsubExecScript(self):
        ''' 
            create the qsub submission script.
        '''
        
        
        exe="qsub -r y"
        
        if self.paused:
            exe+=" -h "
            
        args={'email':'-m a -M %s@blue-bolt.com' % self._os.getenv('USER'),
        'jobname':self.name,
        'wd':self.wd,
        'render_script':self.scripts['render_script']['script'].name,
        'logs_path':self.paths['log_path'],
        'exe':exe,
        'CPUS':self.cpus}
                    
        # Make logs directory
        
        if not self._os.path.isdir(self.paths['log_path']):
            mkfolder(self.paths['log_path'])
            
        
        
        script = '''#!/bin/bash
#
# Submision Script for %s
#            \n''' % (self.scenefile)
        
        
        if not self.email:
            args['email']=''
        
        script+="%(exe)s -l mem_free=4G  %(email)s -N %(jobname)s -o %(logs_path)s -wd %(wd)s %(render_script)s;\n" % (args)
        
        
        f = open(self.paths['scripts_path']+"/"+args['jobname'], 'w')
        f.write(script)
        f.close()
    
        self._os.chmod(self.paths['scripts_path']+"/"+args['jobname'], 0775)
        
        # assign this script to the main script name
        
        self.script=f
        
        return f
            
    def makeScripts(self):
        ''' Generate the render scripts'''
        j_scripts=list()
        j_scripts.append(self.createJobScript())
    
        return j_scripts
    
    def makeJobs(self):
        self.makeScripts()

        if len(self.children):
            return self.children

        return [self]
    

    def output(self):
        ''' generate job infomation output '''
        
        
        output = "submitting job...: %s \n" % ('.'.join([self.label,self.name]))
        output+= "command..........: %s \n" % self.cmd
        output+= "working dir......: %s \n" % self.wd
        output+= "send disabled....: %s \n" % str(self.paused)
        if len(self.dependency_list):
            name_list = []
            for dep in self.dependency_list:
                name_list.append('.'.join([dep.label,dep.name]))
            output+= "depends on.......: %s \n" % ','.join( name_list )
                
        return output
    
    