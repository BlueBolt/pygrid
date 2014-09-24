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

class MayaRenderJob(Job):
    ''' Main Generic Maya Render Job, use this one to do sub instances of maya Render jobs '''
    
    def __init__(self,jid=None):
        super(MayaRenderJob, self).__init__(jid)    
        self.name = 'Maya_render_job'  
        self.label = 'maya_render_job'
        self.type = JobType.ARRAY
        self.queue = Queue('3d.q')
        self.cpus = 2
        self.scenefile = ''
        self.resources = {'mem_free':'4G','maya':'1'}
        self.publish = True
        self.maya_version = '2014'
        self.render_cmd = 'Render'
        self.args = ''
        self.renderer = 'sw' #set the default renderer to mayaSoftware
        self.camera = 'perspShape'
        self.layer = 'defaultRenderLayer'
        self.render_pass = 'beauty'
        self.version=None
        self.res={'width':1920,'height':1080}
        self.slices=0    

    def setJobName(self):
        ''' Generate a time staped name for this Job '''
        dt=self.dt.strftime('%Y%m%d%H%M%S')
        self.name=_os.path.basename(_os.path.splitext(self.scenefile)[0])+"_"+self.layer+"_"+self.render_pass+'.'+str(dt)
        self.prefix=_os.path.basename(_os.path.splitext(self.scenefile)[0])+"_"+self.layer+"_"+self.render_pass
        
    def setVersion(self):
        ''' check and set the version based on the render_tmp location '''
        
        if self.paths.has_key('out_dir'):
            
            if not self.version: # if the version has not been set detect it
                self.version = 1

                print self.paths['out_dir']
                        
                if _os.path.isdir(self.paths['out_dir']):
                    dirlist=_os.listdir(self.paths['out_dir'])
                    dirlist.sort()
                    for d in  dirlist:
                        if d.startswith("v"):
                            self.version = int(d.strip('v'))+1
    
    def publishScene(self):
        ''' make a copy of the input maya file in the working directory '''    
            
        mkfolder(self.paths["mb_path"])
        
        self.scenefile = copyFile(self.scenefile,self.paths["mb_path"])

    def createJobScript(self):
        ''' Generate the bash script  for rendering '''
                
        if not _os.path.isdir(self.paths['scripts_path']):
            mkfolder(self.paths['scripts_path'])
        
        # do the publish
        
        if self.publish:
            self.publishScene()

        # settings #

        img_name = "%s_\<RenderLayer\>_lnh_v%03d" % (self.envs['WORKSPACE'],self.version)
        
        settings={'scenefile':self.scenefile,
        'wd':self.wd,
        'maya':self.maya_version,
        'camera':self.camera,
        'render_cmd':self.render_cmd,
        'renderer':self.renderer,
        'mayaproject':'%s/user/%s/maya' % (self.envs['WORKSPACE_PATH'],self.envs['USER']),
        'image_path':self.paths['img_path'],
        'image_name':img_name,
        'renderlayer':self.layer,
        'slice':self.slices>1,
        'num_slices':self.slices,
        'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
        'CPUS':self.cpus,
        'args':self.args,
        'width':self.res['width'],
        'height':self.res['height'],
        'task_header':' '.join((self.name,self.date,self.scenefile))}
    
        settings['envs'] = ''
        # simple loop over the envs in the self.envs dictionary to add any extra/custom envs to the render script
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
        render_script = open(self.paths['scripts_path'] + "/" + self.label + ".%s"%self.dt.strftime('%Y%m%d%H%M%S') + ".sh", 'w')
        
        render_script.write('''#!/bin/bash
        
#
# %(task_header)s
#    


#$ -S /bin/bash
#$ -j y

umask 0002

#set workspace

source ${SOFTWARE}/bluebolt/envset/workspace %(WORKSPACE_PATH)s

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

cmd="%(render_cmd)s -r %(renderer)s -proj %(mayaproject)s -rl %(renderlayer)s -n $NSLOTS -s $s -e $e -x %(width)s -y %(height)s -rd %(image_path)s -im %(image_name)s -fnc name.#.ext -cam %(camera)s %(args)s %(scenefile)s;"
echo $cmd
#Run it
function this_task(){

time %(render_cmd)s -r %(renderer)s -proj %(mayaproject)s -rl %(renderlayer)s -n $NSLOTS -s $s -e $e -x %(width)s -y %(height)s -rd %(image_path)s -im %(image_name)s -fnc name.#.ext -cam %(camera)s %(args)s %(scenefile)s;

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task

''' % (settings))
        
        render_script.close()
        
        self.script = render_script.name
        
        return render_script
    
    def setPaths(self):
        ''' Set the paths for pantry based resources '''
        
        #
        # Changed for the renders to go to the user directory
        #

        if not 'out_dir' in self.paths : self.paths['out_dir']="%s/renders/%s/%s/" % (self.envs['USER_PATH'],self.layer,self.render_pass)
        
        # everything below relys on the version being set
        self.setVersion()

        self.paths['pantry'] = _os.path.join(self.paths['out_dir'],"v%03d"%self.version,'.pantry')

        self.setWD(self.paths['pantry'])

        mkfolder(self.wd)
                
        self.paths['mb_path'] = '%s/mb' % self.wd
        
        self.paths['scripts_path'] = '%s/scripts' % self.wd
        
        if not 'img_path' in self.paths : self.paths['img_path'] = "%s/v%03d/%s" % (str(self.paths['out_dir']),int(self.version),'x'.join( map(str, self.res.values()) ) )
        
    def setOutDir(self,out_dir):
        """
        Set the output directory for the renders , this will reset the version to None and autoset up the child folders
        """

        self.paths['out_dir']=out_dir
        self.version=None
        self.setPaths()

    def setOutImagePath(self,out_image_path):

        self.paths['img_path'] = out_image_path

    def makeJobs(self):

        # set the job name
        
        self.setJobName()

        self.setPaths()
        
        fldr_args={'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
        'USER':self.envs['USER'],
        'jobname':self.name,
        'label':self.label}
        
        self.createJobScript()

    def output(self):
        ''' generate job infomation output '''
        
        env_list = list()
        for k in self.envs: env_list.append( "%s=%s" % (k,self.envs[k]) )
                
        self.extra_data={
                        'scenefile':self.scenefile,
                        'maya_version':self.maya_version,
                        'frames':self.frames,
                        'env': ';'.join(env_list),
                        'layer':self.layer,
                        'pass':self.render_pass                 
                        }
                
        output = "submitting job...: %s \n" % self.name
        output = "version..........: %d \n" % self.version
        output+= "command..........: %s \n" % self.cmd
        output+= "working dir......: %s \n" % self.wd
        output+= "send disabled....: %s \n" % str(self.paused)
                
        return output
