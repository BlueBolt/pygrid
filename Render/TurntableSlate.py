#******************************************************************************
# (c)2012 BlueBolt Ltd.  All rights reserved.
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
# Author:Fernando Vizoso Martinez - fernando-m@blue-bolt.com
# 
# File:TurntableSlate.py
# 
# 
#******************************************************************************


from gridengine.Job import Job
from gridengine.Job import mkfolder
from gridengine.Queue import Queue
from gridengine.Utils import copyFile

from gridengine.Render.Arnold import KickJob, MayaAssGenJob
from gridengine.Render.Nuke import NukeRenderJob


from Command import CommandJob

import os as _os 


class TurntableSlateJob(Job):
    ''' Main Arnold job class this is the parent of any ass generator or kick render job'''
    
    def __init__(self, jid=None):
        self.label = 'turntable'
        self.queue=Queue('mkdaily.q')
        self.cleanup = False
        self.seqcheck = False        
        self.publish = True
        self.updatedVersion=False
        
        self.scenefile = '' # can be maya ma/mb or arnold ass file
        self.arnold_version = '4.0.7.0'
        self.maya_version = '2012'
        self.mtoa_version = '0.18.0'
        self.version = 1 # use to override the version that is sent/rendered.
        self.slices = 0
        
        self.prefix = ''
        self.outFrames = ""
        self.use_showAOVS = False
        
        #scene options
        self.layer = 'defaultRenderLayer'
        self.renderlayer = self.layer 
        self.render_pass = 'BEAUTY_PASS'
        self.camera = 'perspShape'
        self.aovs = {'beauty':{'aovs':['rgba'], 'half_float':True, 'premult':True}}
                
        # Kick options
        self.image_scale = 1.0
        self.verbosity = 2
        self.res = {'width':1920, 'height':1080}        
        self.aas = 4 # anti-aliasing samples default:4 draft:2 production:8
        self.bs = 64 # arnold bucket sizes
        self.subd = 999 # set the max subdivision surface level
        
        # kick disable options
        self.disable_textures = False
        self.disable_shaders = False
        self.disable_background = False
        self.disable_atmosphere = False
        self.disable_lights = False
        self.disable_shadows = False
        self.disable_subds = False
        self.disable_displacement = False
        self.disable_bump = False
        self.disable_motion_blur = False
        self.disable_sss = False
        self.disable_direct_lighting = False
    
        #nuke options
        self.render_cmd = "/software/wrappers/nuke"
        self.args = ""
        self.options = ' -l nk=1'
        self.furnace = False
        self.nuke_version = '6.3v5'
        self.cpus = 8
        self.proxy = False        
        self.nukescript = ''
        self.views = ['main']    
        self.write = 'Write1'
        self.nukestep=1000
        # Set the default versions based upon current environment
        
        if _os.environ.has_key('NUKE_VERSION'):
            self.nuke_version = _os.environ['NUKE_VERSION']
        
        super(TurntableSlateJob, self).__init__(jid)
 
    def setJobName(self):
        ''' Generate a time stamped name for this Job '''
        dt = self.dt.strftime('%Y%m%d%H%M%S')
        self.prefix = _os.path.basename(_os.path.splitext(self.scenefile)[0]) + "_" + self.layer + "_" + self.render_pass
        self.name = self.prefix + '.' + str(dt)
    
    
    def setVersion(self):
        ''' check and set the version based on the render_tmp location '''
        
        if self.paths.has_key('out_dir'):
            self.version = 1
            if _os.path.isdir(self.paths['out_dir']):
                dirlist = _os.listdir(self.paths['out_dir'])
                dirlist.sort()
                for d in  dirlist:
                    ver=d.strip('v').strip("_published")
                    if ver.isdigit():
                        self.version = int(ver) + 1    # legacy published version folders 
    
            self.setVersionWD()
    
    def setVersionWD(self):
        ''' set the working directory based on the version given'''
        
        self.setWD('%s/%s/%s/%s/v%03d' % (self.paths['pantry'],
                                            self.camera.split(':')[-1],
                                            self.layer,
                                            self.render_pass,
                                            self.version))
        
    def setPaths(self):
        ''' Set the paths for pantry based resources (tdls,sdls,shadowmaps) '''
        
        self.paths['out_dir'] = ''
        
        if '3d_builds' in _os.path.abspath(self.envs['WORKSPACE_PATH']):
            self.paths['out_dir'] = "%s/render_tmp/%s/%s/%s/" % (self.envs['WORKSPACE_PATH'], self.camera.split(':')[-1], self.layer, self.render_pass)
        else:
            self.paths['out_dir'] = "%s/3d/render_tmp/%s/%s/%s/" % (self.envs['WORKSPACE_PATH'], self.camera.split(':')[-1], self.layer, self.render_pass)
        
        self.paths['pantry'] = '%(SHOW_PATH)s/3d/pantry/%(SHOT)s' % (self.envs)
        if self.updatedVersion==False:
            self.setVersion()
            self.updatedVersion=True
        if not _os.path.exists("%s/v%03d" % (self.paths['out_dir'], self.version)):
            mkfolder("%s/v%03d" % (self.paths['out_dir'], self.version))
        
        self.paths['ass_path'] = '%s/ass' % self.wd
        
        self.paths['mb_path'] = '%s/mb' % self.wd
        
        self.paths['scripts_path'] = '%s/scripts' % self.wd
        
        self.paths['img_path'] = "%s/v%03d/%s/" % (str(self.paths['out_dir']), int(self.version), 'x'.join(map(str, self.res.values())))
        
        self.paths['img_beauty_path'] = "%s/v%03d/%s/%s_masterLayer_lnh_v%03d.####.exr" % (str(self.paths['out_dir']), int(self.version), 'x'.join(map(str, self.res.values())),self.asset,int(self.version))
        
        if self.dailyOutput!='True':
            qtBasepath='%s/v%03d/turntable' % (self.paths['out_dir'],int(self.version))
            self.paths['qt_path']='%s/%s_turntable_v%03d.mov' % (qtBasepath,self.asset,int(self.version))
        else:
            qtBasepath=_os.path.join(self.envs['SHOW_PATH'],'dailies',self.envs['SCENE'],self.envs['SHOT'],self.discipline,'internal','v%03d'%self.version)
            self.paths['qt_path']='%s/%s_turntable_v%03d.mov' % (qtBasepath,self.asset,int(self.internalVersion))
            
        if not _os.path.exists(qtBasepath):
            _os.makedirs(qtBasepath)
            
    def setWorkingDirectory(self):
        ''' try and set the working directory for output logs and scripts etc based on set environment variables '''
        
        # get the show and shot paths
        
        self.getEnvs()
                        
        self.paths['pantry'] = '%(SHOW_PATH)s/3d/pantry/%(SHOT)s' % (self.envs)
        
        #set
        
        
        return True        
    
    
    def createMayaAssGenJob(self):
        ''' Make a job to generate a .ass file from a maya scene '''
        
        ass_job = MayaAssGenJob()
        ass_job.name = self.name        
        ass_job.frames = self.frames
        ass_job.layer = self.layer
        ass_job.renderlayer = self.layer
        ass_job.camera = self.camera
        ass_job.queue = self.queue    
        ass_job.scenefile = self.scenefile
        ass_job.version = self.version
        ass_job.cpus = 1    
        ass_job.maya_version = self.maya_version
        ass_job.arnold_version = self.arnold_version
        ass_job.mtoa_version = self.mtoa_version
        ass_job.render_pass = self.render_pass
        ass_job.res = self.res
        ass_job.wd = self.wd
        ass_job.paths = self.paths
        ass_job.envs = self.envs
        ass_job.parent = self
        ass_job.paused = self.paused
        ass_job.publish = self.publish
        ass_job.queue = Queue('3d.q')
        return ass_job 
    
    def publishScene(self):
        ''' make a copy of the input nuke script in the working directory '''    
    
        nk_dir = '%s/nk' % self.wd
        
        mkfolder(nk_dir)
        
        self.nukescript = copyFile(self.nukescript,nk_dir)
        
    def createNukeJob(self):
        """ Make a NukeRenderJob instance """
        
        self.publishScene()
        nuke_job = NukeRenderJob()
        
        nuke_job.name = self.name    
        nuke_job.cpus = 2
        #nuke_job.frames = '%s-%s'%(self.frames.split('-')[0],int(self.frames.split('-')[1])+1)
        nuke_job.frames=self.frames
        nuke_job.step = self.step
        nuke_job.max_slots = self.max_slots
        nuke_job.wd = self.wd        
        nuke_job.paths = self.paths
        nuke_job.envs = self.envs  

        nuke_job.step=self.nukestep
        nuke_job.parent = self # make sure that the nuke script is set a child of this script
        nuke_job.queue=Queue('mkdaily.q')
        nuke_job.furnace = self.furnace
        nuke_job.nukescript = self.nukescript
        nuke_job.script = self.nukescript
        
        nuke_job.proxy = self.proxy
        nuke_job.views = self.views              
        nuke_job.envs['IN_FILE_NAME']=self.paths['img_beauty_path']
        nuke_job.envs['OUT_FILE_NAME']=self.paths['qt_path']
        nuke_job.envs['DAILY_VERSION']='v%03d'%(self.version)
        nuke_job.envs['SLATE_NOTE']='%s_v%03d'%(self.asset,int(self.version))

        
        if self.furnace:
            nuke_job.options =' -l nk_fn=1' 
        
        nuke_job.options += self.options
        
        return nuke_job
       
    
    def createKickJob(self):
        ''' Make main kick job instance '''
        
        kick_job = KickJob()
        
        # Grid stuff
        kick_job.name = self.name    
        kick_job.wd = self.wd        
        kick_job.paths = self.paths
        kick_job.envs = self.envs
        kick_job.queue = self.queue    
        kick_job.paused = self.paused
        kick_job.cpus = self.cpus
        kick_job.max_slots = self.max_slots
        kick_job.queue = Queue('3d.q')
        kick_job.camera = self.camera
        kick_job.publish = self.publish
                
        
        kick_job.res = self.res
        kick_job.image_scale = self.image_scale
        kick_job.verbosity = self.verbosity
        
        kick_job.aas = self.aas
        kick_job.bs = self.bs
        kick_job.subd = self.subd
        
        # kick disable options
        kick_job.disable_textures = self.disable_textures
        kick_job.disable_shaders = self.disable_shaders
        kick_job.disable_background = self.disable_background
        kick_job.disable_atmosphere = self.disable_atmosphere
        kick_job.disable_lights = self.disable_lights
        kick_job.disable_shadows = self.disable_shadows
        kick_job.disable_subds = self.disable_subds
        kick_job.disable_displacement = self.disable_displacement
        kick_job.disable_bump = self.disable_bump
        kick_job.disable_motion_blur = self.disable_motion_blur
        kick_job.disable_sss = self.disable_sss
        kick_job.disable_direct_lighting = self.disable_direct_lighting
        
        kick_job.arnold_version = self.arnold_version
                
        kick_job.frames = self.frames
        #kick_job.args = self.args # add any custom arguments to the kick commandline
        
        kick_job.scenefile = self.scenefile
        
        kick_job.parent = self        
                
        
        return kick_job    
        
    def createCleanUpJob(self):
        ''' Make the Clean up job that relies up on the the end of the main kick render  '''

        cleanup_job = CommandJob()
        
        cleanup_job.parent = self
        
        return cleanup_job
    
    def makeJobs(self): 
        ''' Generate the child Jobs for submission and assign thier dependencies 
        
            This method will call automatically setPaths() and setJobName()
            
            
        '''
    
        # set the file paths for scripts etc
    
        self.setPaths()
    
        # set the job name
        
        self.setJobName()
            
        # Check the input file, if it's a maya file make the ASS gen Job, return the .ass file that should be 
        # sent to the KickJob
        
        r_file = self.scenefile
        
        ass_job = None
        
        if _os.path.splitext(r_file.lower())[1] in ('.mb', '.ma'): # is the input scenefile a maya file? If so make a MayaAssGenjob
            ass_job = self.createMayaAssGenJob()
            self.children.append(ass_job)
            
            ass_job.createJobScript() # run the job script generator this should fill in any extra details needed later
                        
            self.scenefile = ass_job.ass_file
            
        # Now make the Kick Job, if necceceary set the dependence on the above AssGenJob
        
        if '.ass' in self.scenefile.lower():

            kick_job = self.createKickJob()
            
            if ass_job:
                kick_job.dependency = ass_job
                kick_job.publish_scene = False # we don't want to publish any ass files from this automatic job
            
            kick_job.createJobScript()
            
            self.children.append(kick_job)        
            
            # Add now the Clean-Up Job which depends on the kick job        
            
            if self.cleanup:
                cleanup_job = self.createCleanUpJob()
                
                cleanup_job.dependency = kick_job
                
                cleanup_job.createJobScript()
                
            
            
            nuke_job = self.createNukeJob()
            nuke_job.dependency = kick_job
            nuke_job.createJobScript()
            
            self.children.append(nuke_job)
        else:
            raise NoAssFileError(self.scenefile)
           
    def output(self):
        ''' generate job infomation output '''
        
        self.extra_data = {
                        'scenefile':self.scenefile,
                        'maya_version':self.maya_version,
                        'arnold_version':self.arnold_version,
                        'frames':self.frames
                        }
        
        output = "submitting job...: %s \n" % self.name
        output += "command..........: %s \n" % self.cmd
        output += "working dir......: %s \n" % self.wd
        output += "send disabled....: %s \n" % str(self.paused)
        if self.dependency:
            output+= "depends on ....: %s \n" % self.dependency.label
        return output
