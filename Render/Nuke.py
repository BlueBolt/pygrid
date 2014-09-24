
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
    Main nuke class

''' 
from gridengine.Job import Job,JobType
from gridengine.Job import mkfolder
from gridengine.Queue import Queue
from gridengine.Utils import copyFile

from gridengine.Exceptions import *

import Command

import os as _os 

class NukeRenderJob(Command.CommandJob):
    ''' Job that renders the choosen SINGLE write node '''
    
    def __init__(self,jid=None):
        super(NukeRenderJob, self).__init__(jid)
        self.name='nuke_job_name'
        self.label='nuke_job'
        self.type=JobType.ARRAY
        self.render_cmd = "${SOFTWARE}/wrappers/nuke"
        self.args = ""
        self.options = ' -l nk=1'
        self.furnace = False
        self.bblibrary = False
        self.nuke_version = '6.3v5'
        self.queue = Queue('2d.q')
        self.verbosity = 1
        self.cpus = 4
        self.proxy = False        
        self.nukescript = ''
        self.views = []   
        self.write = None
        self.wd=None
        

        # Set the default versions based upon current environment
        
        if _os.environ.has_key('NUKE_VERSION'):
            self.nuke_version = _os.environ['NUKE_VERSION']

            
        
    def createJobScript(self):
        ''' Make the render script for starting the kick job '''
        
        # the prescript for setting up a start-end range for the task
        self.prescript = '''
        
#set workspace


source ${SOFTWARE}/bluebolt/config/workspace.env

eval workspace -no-hi %s

s=$SGE_TASK_ID
e=`echo $[$s+$SGE_TASK_STEPSIZE-1]`
if [ $e -ge $SGE_TASK_LAST ]; then
    e=$SGE_TASK_LAST;
fi


echo START :: $s
echo END :: $e

export START=$s
export END=$e

''' % self.envs['WORKSPACE_PATH']

        # set nuke options        
        
        self.args += " -m $NSLOTS" # set the custom args for the renderer
        
        if self.write:
            self.args += " -X %s" % self.write
        else:
            # most of the time we will not be sending this kind of job this is just here if we need a direct quick nuke job.
            self.args += " -x" 

        if self.proxy:
            self.args = " -p"
        else:
            self.args += " -f"
        
        self.args += " -cont" 

        self.args += " -V %d" % self.verbosity
        
        if len(self.views):
            self.args += " -view %s" % ','.join(self.views)
        
        self.args += " -F $s-$e"
                
        # do any additional envs that might be needed
        
        self.envs['NUKE_VERSION'] = self.nuke_version

        if _os.environ.has_key('OCIO_VERSION'):
            self.envs['OCIO_VERSION'] = _os.environ['OCIO_VERSION']

        if _os.environ.has_key('LD_PRELOAD'):
            self.envs['LD_PRELOAD'] = _os.environ['LD_PRELOAD']
        
        # TODO: for now we are not taking in to account dependencies
        # TODO: we need to add the ability to run python scripts on the nuke script with optional arguments
        
        self.cmd = '%s %s %s' % (self.render_cmd,self.args,self.nukescript)
                
        super(NukeRenderJob,self).createJobScript()
        
        return self.script
 
class NukeJob(Job):
    ''' Nuke instance of gridengine submitting job class '''
    
    def __init__(self,jid=None):
        super(NukeJob, self).__init__(jid)
        self.name = 'nuke_job' #: name of this job (gets auto filled by @setJobName)
        self.label = 'nuke' #: label for the job as it will appear in bb_grid
        self.nuke_version = '6.3v5' #: version of nuke to use
        self.queue = Queue('2d.q') #: queue that these jobs will be sent to value as an object
        self.cpus = 4 #: number of cpus to use on a single machine
        self.nukescript = '' #: the nuke script to run
        self.publish = True #: should the nukescript be coped somewhere to run?
        
        # list of write nodes 
        self.writes = {} #: list of names of Write nodes and views to execute e.g {'Write1':['main']}
        self.proxy = False #: enable to render in proxymode
        self.furnace = False #: this job uses furnace plugin nodes
        self.bblibrary = False
        self.scripts={}
        self.wd=None
        self.verbosity = 2
        
    
    def setJobName(self):
        ''' Generate a time stamped name for this Job '''
        dt=self.dt.strftime('%Y%m%d%H%M%S')
        self.prefix=_os.path.basename(self.nukescript.strip('.nk'))
        self.name=self.prefix+'.'+str(dt)
       
    def publishScene(self):
        ''' make a copy of the input nuke script in the working directory '''    
    
        nk_dir = '%s/nk' % self.wd
        
        mkfolder(nk_dir)
        
        self.nukescript = copyFile(self.nukescript,nk_dir)
        
    def createNukeJob(self):
        """ Make a NukeRenderJob instance """
        
        nuke_job = NukeRenderJob()
        
        nuke_job.nuke_version = self.nuke_version
        nuke_job.name = self.name    
        nuke_job.cpus = self.cpus
        nuke_job.frames = self.frames
        nuke_job.step = self.step
        nuke_job.queue = self.queue
        nuke_job.max_slots = self.max_slots
        nuke_job.wd = self.wd        
        nuke_job.paths = self.paths
        nuke_job.envs = self.envs  
        nuke_job.paused = self.paused
        nuke_job.verbosity = self.verbosity

        
        nuke_job.parent = self # make sure that the nuke script is set a child of this script
        
        nuke_job.furnace = self.furnace
        nuke_job.bblibrary = self.bblibrary
        nuke_job.nukescript = self.nukescript
        nuke_job.proxy = self.proxy            

        if self.furnace:
            nuke_job.options +=' -l nk_fn=1' 
            self.label = 'nuke-furnace'

        if self.bblibrary:
            nuke_job.options +=' -l bb_lib=1' 
            self.label = 'nuke-bblibrary'

        nuke_job.options += self.options
        
        return nuke_job
    
    def makeJobs(self):
        """ Generate the child Jobs for submission and assign thier dependencies  """
              
        # set the job name
        
        self.setJobName()

        print self.name

        if self.wd==None:
        
            fldr_args={'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
            'USER':self.envs['USER'],
            'jobname':self.name}
            
            self.setWD("%(WORKSPACE_PATH)s/user/%(USER)s/nuke/scripts/render/%(jobname)s" % fldr_args) # set the working directory for this job, to the users dir + 'render'
             
                
        if self.publish:
            self.publishScene()

        if not len(self.writes):
            raise JobError("No Write nodes are set to be executed")
    
        for w in self.writes:
        
            nuke_job = self.createNukeJob()
            
            nuke_job.write = w

            nuke_job.views = self.writes[w] 
            
            nuke_job.name = '.'.join([self.name,w])
            
            nuke_job.label = '.'.join([self.label,w])
            
            nuke_job.createJobScript()
            
            self.children.append(nuke_job)
  
        
        return self.children
    
    def setExtraData(self):
        """ set the extra_data dictionary for the grid interface""" 
    
        self.extra_data={
            'nuke_script':self.nukescript,
            'nuke_version':self.nuke_version,
            'frames':self.frames,
            'writes':','.join(self.writes),
            'outputpaths':''
        }
        
        
        
        
    def output(self):
        ''' Submit this job to gridengine '''
        
        self.setExtraData()
        
        output = "submitting job...: %s \n" % self.name
        output+= "working dir......: %s \n" % self.wd
        output+= "nukescript.......: %s \n" % self.nukescript
        output+= "step.............: %d \n" % int(self.step)
        output+= "cpus.............: %d \n" % int(self.cpus)
        output+= "queue............: %s \n" % self.queue
        output+= "writes...........: %r \n" % self.writes
        output+= "nuke version.....: %s \n" % self.nuke_version
        output+= "proxy............: %s \n" % str(self.proxy)
        output+= "send disabled....: %s \n" % str(self.paused)
        output+= "frames...........: %s \n" % self.frames
                
        if len(self.dependency_list):
            name_list = []
            for dep in self.dependency_list:
                name_list.append(dep.name)
            output+= "depends on.......: %s \n" % ','.join( name_list )
            
        return output
    
