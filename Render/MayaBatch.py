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
# File:maya_render.py
# 
# 
#******************************************************************************

'''

    Generic maya render job class, used by other renderers for running pre-flight and generic render commands.

'''

from gridengine.Job import Job,JobType,mkfolder
from gridengine.Queue import Queue
from gridengine.Utils import copyFile

import os as _os

class MayaBatchJob(Job):
    ''' Main Generic Maya Batch Job, use this one to do sub instances of maya Batch processes '''
    
    def __init__(self,jid=None):
        super(MayaBatchJob, self).__init__(jid)    
        self.name = 'Maya_Batch_job' 
        self.label = 'MayaBatchJob'
        self.type = JobType.ARRAY
        self.queue = Queue('3d.q')
        self.cpus = 2
        self.scenefile = 'invalid_scene.mb'
        self.maya_version = '2012'
        self.render_cmd = '${SOFTWARE}/wrappers/maya'
        self.publish = True
        self.args = ''
        self.camera = 'perspShape'
        self.layer = 'defaultRenderLayer'
        self.render_pass = 'BEAUTY_PASS'
        self.version=1
        self.res={'width':'1920','height':'1080'}
        self.slices=0
    
    def setJobName(self):
        ''' Generate a time staped name for this Job '''
        dt=self.dt.strftime('%Y%m%d%H%M%S')
        self.name=_os.path.basename(_os.path.splitext(self.scenefile)[0])+'.'+str(dt)
        self.prefix=_os.path.basename(_os.path.splitext(self.scenefile)[0])
        
    def publishScene(self):
        ''' make a copy of the input maya file in the working directory '''    
    
        mb_dir = '%s/mb' % self.wd
        
        mkfolder(mb_dir)
        
        self.scenefile = copyFile(self.scenefile,mb_dir)

        return self.scenefile
        
    def createJobScript(self):
        ''' Generate the bash script  for rendering '''
                
        if not _os.path.isdir(self.paths['scripts_path']):
            mkfolder(self.paths['scripts_path'])
        
        # do the publish
        
        if self.publish:
            self.publishScene()
        
        # settings #
        
        settings={'scenefile':self.scenefile,
        'wd':self.wd,
        'maya':self.maya_version,
        'camera':self.camera,
        'render_cmd':self.render_cmd,
        'mayaproject':'%s/user/%s/maya' % (self.envs['WORKSPACE_PATH'],self.envs['USER']),
        'args':self.args,
        'slice':self.slices>1,
        'num_slices':self.slices,
        'CPUS':self.cpus,
        'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
        'task_header':' '.join((self.name,self.date,self.scenefile))}
    
        settings['envs'] = ''
        # simple loop over the envs in the self.envs dictionary to add any envs to the render script
        for e in self.envs.keys():
            settings['envs'] += 'export %s=%s;\n' % (e,self.envs[e])
                
        settings['taskscript']='''
s=$SGE_TASK_ID
e=`echo $[$s+$SGE_TASK_STEPSIZE-1]`
if [ $e -ge $SGE_TASK_LAST ]; then
    e=$SGE_TASK_LAST;
fi


echo START :: $s
echo END :: $e

'''
        
        #Slicing settings
        if self.slices>1:
            settings['taskscript']='''

s=%d
e=%d

echo START :: $s
echo END :: $e

export SLICE="true"
echo SLICE :: $SLICE

export SLICE_PADDED=`printf "%%02d" $SGE_TASK_ID`

            ''' % (self.start, self.start)
                
    
        #Generate preflight BASH script
        render_script = open(self.paths['scripts_path'] + "/" + self.label + ".%s"%self.dt.strftime('%Y%m%d%H%M%S')  + ".sh", 'w')
        
        render_script.write('''#!/bin/bash
        
#
# MAYA Batch job - %(task_header)s
#    


#$ -S /bin/bash
#$ -j y
#$ -l maya=1

umask 0002

#set workspace

source ${SOFTWARE}/bluebolt/config/workspace.env

eval workspace -no-hi %(WORKSPACE_PATH)s

export MAYA_APP_DIR=${TMPDIR}/maya;
export MAYA_VERSION=%(maya)s;
export MAYA_MAJOR_VERSION=%(maya)s;
export MAYA_LOCATION=$SOFTWARE/maya/$UNAME.$DIST.$ARCH/%(maya)s;

%(envs)s

echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH

unset SLICE
unset SLICE_PADDED

%(taskscript)s

export START=$s
export END=$e

function this_task(){

cmd="%(render_cmd)s -batch -proj %(mayaproject)s -file %(scenefile)s %(args)s"
echo $cmd
#Run it
time $cmd

exitstatus=$?

if [ $exitstatus != 0 ];then
return 100
fi

return $exitstatus

}

eval this_task

''' % (settings))
        
        render_script.close()
        
        self.script = render_script.name
        
        return render_script
    
        
        
    def makeJobs(self):
        """ Generate the child Jobs for submission and assign thier dependencies  """
              
        # set the job name
        
        self.setJobName()
        
        fldr_args={'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
        'USER':self.envs['USER'],
        'jobname':self.name,
        'label':self.label}
        
        self.setWD("%(WORKSPACE_PATH)s/user/%(USER)s/%(label)s/grid_jobs/%(jobname)s" % fldr_args) # set the working directory for this job, to the users dir + 'render'
                             
                             
        self.createJobScript()
    
        return self
    
    def output(self):
        ''' Submit this job to gridengine '''
        
        self.extra_data={
            'maya_scene':self.scenefile,
            'maya_version':self.maya_version
        }
        
        
        output = "submitting job...: %s \n" % ('.'.join([self.label,self.name]))
        output+= "working dir......: %s \n" % self.wd
        output+= "Maya File........: %s \n" % self.scenefile
        output+= "Maya Version.....: %s \n" % self.maya_version
        output+= "step.............: %d \n" % int(self.step)
        output+= "cpus.............: %d \n" % int(self.cpus)
        output+= "queue............: %s \n" % self.queue.name
        output+= "send disabled....: %s \n" % str(self.paused)
        output+= "frames...........: %s \n" % self.frames
                
        return output
        
