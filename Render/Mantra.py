
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


#################
#
#   Example of an array job class
#
################### 



from gridengine.Job import Job
from gridengine.Job import mkfolder
from gridengine.Queue import Queue
from gridengine.Exceptions import *

from Command import CommandJob

import os as _os 



class MantraJob(CommandJob):
    ''' Job that does the Arnold standalone render with the kick application '''
    def __init__(self,jid=None):
        super(MantraJob, self).__init__(jid)
        
        self.label = "mantra"
        self.type = JobType.ARRAY
        self.queue = Queue("3d.q")
        self.scenefile = "test.0001.ifd"
        self.mantra_version = "12.1.185"
        self.render_cmd = "${SOFTWARE}/wrappers/mantra"
        self.version = None # use to override the version that is sent/rendered.
        self.args = ""
        self.options = " -l mantra=1" # add mantra resource request
        self.frames = "1-10"
        self.step = 1
        self.publish_scene = False
        
        # mantra options
        self.verbosity = 2 # 1..9, 2 = progress messages
        self.res = {'width':'1920','height':'1080'}  
        self.sample = 4 # anti-aliasing samples default:4 draft:2 production:8
        self.bs = 64 # set the bucket size                     
        
        # Set the default versions based upon current environment
        
        if _os.environ.has_key('HOUDINI_VERSION'):
            self.mantra_version = _os.environ['HOUDINI_VERSION']
        
    def setJobName(self):
        ''' Generate a time stamped name for this Job '''
        super(MantraJob, self).setJobName()
        dt=self.dt.strftime('%Y%m%d%H%M%S')
        self.prefix=_os.path.basename(self.scenefile).split('.')[0]
        self.name=self.prefix+'.'+str(dt)
            
    def publishScene(self):
        ''' make a copy of the input ass file in the working directory '''    
        
        pass
    
    def createJobScript(self):
        ''' Make the render script for starting the kick job '''
        
        self.prescript = '''
s=$SGE_TASK_ID
e=`echo $[$s+$SGE_TASK_STEPSIZE-1]`
if [ $e -ge $SGE_TASK_LAST ]; then
    e=$SGE_TASK_LAST;
fi


echo START :: $s
echo END :: $e

export START=$s
export END=$e

'''
        
        
        self.args += " -j $NSLOTS" # set the custom args for the renderer
        
        self.args += " -V %da" % self.verbosity # set the verbosity
                
        imager_options=[]
        if self.samples != None:
            imager_options.append( "sample=%d" % self.samples )# set the anti-aliasing samples
        
        if self.res != None:
            imager_options.append( "resolution=%(width)dx%(height)d" % self.res )# set the resolution
                
        if self.bs != None:
            imager_options.append( "bucket=%d" % self.bs )# set the bucketsize


        if len(imager_options):
            self.args += " -I %s" % ','.join(imager_options)
                
        if len(self.frames.split('-')) > 1:
            # Set the step to 1 as Mtoa would have spit out a file per frame
            self.step = 1      
            # change pre script as such to add a padded number for this frame
            self.prescript += '''
f=`printf "%04d" $SGE_TASK_ID`
'''     
            #split the scenefile from it's extension
            scene_file_dirname = _os.path.dirname(self.scenefile)
            scene_file_basename = _os.path.basename(self.scenefile)

            split_scenename = scene_file_basename.split('.')
            split_scenename[1] = '$f'
            this_sn = '.'.join(split_scenename)
            
            self.scenefile = _os.path.join(scene_file_dirname,this_sn)
            
        # override the Command.cmd variable
        self.cmd = '%s %s -F %s' % (self.render_cmd,self.args,self.scenefile)
                
        super(MantraJob,self).createJobScript()
        
        return self.script

    
    
    def setVersion(self):
        ''' check and set the version based on the render_tmp location '''
        
        if self.paths.has_key('out_dir'):
            
            if not self.version: # if the version has not been set detect it
                self.version = 1
                        
                if _os.path.isdir(self.paths['out_dir']):
                    dirlist=_os.listdir(self.paths['out_dir'])
                    dirlist.sort()
                    for d in  dirlist:
                        self.version = int(d.strip('v').strip("_published"))+1    # legacy published version folders 
    
    
    def setVersionWD(self):
        ''' set the working directory based on the version given'''
        
        self.setWD(self.paths['pantry'])
        
    def setPaths(self):
        ''' Set the paths for pantry based resources (tdls,sdls,shadowmaps) '''
        
        #
        # Changed for the renders to go to the user directory
        #
        
        self.paths['out_dir']=''
        
        # This will be obsolete
        # if '3d_builds' in _os.path.abspath(self.envs['WORKSPACE_PATH']):
        #     self.paths['out_dir']="%s/render_tmp/%s/%s/%s/" % (self.envs['WORKSPACE_PATH'],self.camera.split(':')[-1],self.layer,self.render_pass)
        # else:
        #     self.paths['out_dir']="%s/3d/render_tmp/%s/%s/%s/" % (self.envs['WORKSPACE_PATH'],self.camera.split(':')[-1],self.layer,self.render_pass)
        
        self.paths['out_dir']="%s/%s/mantra/" % (self.envs['USER_PATH'],self.envs['USER'])
        
        # everything below relys on the version being set
        self.setVersion()
        
        mkfolder("%s/v%03d" % (self.paths['out_dir'],self.version))

        self.paths['pantry'] = _os.path.join(self.paths['out_dir'],"v%03d"%self.version,'.pantry')
                
        self.paths['scripts_path'] = '%s/scripts' % self.wd
        
        self.paths['img_path'] = "%s/v%03d/%s/" % (str(self.paths['out_dir']),int(self.version),'x'.join( map(str, self.res.values()) ) )

        self.setVersionWD()

    def makeJobs(self):

        # set the file paths for scripts etc
    
        self.setPaths()
    
        # set the job name
        
        self.setJobName()

        # creaste the job script

        self.createJobScript()

        return self
    
    def output(self):
        ''' generate job infomation output '''
        
        
        output = "submitting job...: %s \n" % self.name
        output+= "command..........: %s \n" % self.cmd
        output+= "working dir......: %s \n" % self.wd
        output+= "send disabled....: %s \n" % str(self.paused)
        if len(self.dependency_list):
            name_list = []
            for dep in self.dependency_list:
                name_list.append(dep.name)
            output+= "depends on.......: %s \n" % ','.join( name_list )
                
        return output

        
    
