
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
    Main maya MentalRay class

    has one job:
     
     render_mr -- do the render

''' 
from gridengine.Job import Job,JobType
from gridengine.Job import mkfolder
from gridengine.Queue import Queue
from gridengine.Utils import copyFile
from gridengine.Exceptions import *
import os , shutil
import datetime

class MayaMRJob(Job):
    ''' Maya Mental Ray instance of gridengine submitting class '''
    
    def __init__(self):
        super(MayaMRJob, self).__init__()   
        self.name='Maya_mr_job'
        self.label='maya_mr'
        self.type = JobType.ARRAY
        self.queue=Queue('3d.q')
        self.cleanup=False
        self.seqcheck=False
        self.combine_exr=True
        self.publishscene=False
        self.cpus=2
        self.scenefile=''
        self.resources={'mem_free':'4G','mr':'1'}
        self.maya_version='2012'
        self.layer='defaultRenderLayer'
        self.bake_layer='defaultRenderLayer'
        self.render_pass='beauty'
        self.camera='perspShape'
        self.version=-1
        self.res={'width':1920,'height':1080}
        self.slices=0
        self.render_cmd='Render'
        self.prefix=''
        self.scripts={}
        
    
    def setversion(self):
        ''' check and set the version based on the render_tmp location '''
        
        if self.paths.has_key('out_dir'):
            if self.version == -1 and os.path.isdir(self.paths['out_dir']):              
                dirlist=os.listdir(self.paths['out_dir'])
                dirlist.sort()
                for d in  dirlist:
                    try:
                        self.version = int(d.strip('v').strip("_published"))+1  
                    except ValueError:
                        pass
            
            
        
        
    def setJobName(self):
        dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.name=os.path.basename(self.scenefile.strip('.mb').strip('.ma'))+"_"+self.layer+"_"+self.render_pass+'.'+str(dt)
        self.prefix=os.path.basename(self.scenefile.strip('.mb').strip('.ma'))+"_"+self.layer+"_"+self.render_pass
        
    def setPaths(self):
        ''' Set the paths for pantry based resources (tdls,sdls,shadowmaps) '''
                
        if not 'out_dir' in self.paths : self.paths['out_dir']="%s/renders/%s/%s/" % (self.envs['USER_PATH'],self.layer,self.render_pass)
              
        # self.paths['pass_path']='%s/%s/%s/%s' % (self.paths['out_dir'],self.layer,self.render_pass,self.camera.split(':')[-1])
                
        self.setversion()

        self.paths['pantry'] = os.path.join(self.paths['out_dir'],"v%03d"%self.version,'.pantry')
        
        self.setWD(self.paths['pantry'])
        mkfolder(self.wd)
        
        self.paths['mb_path']='%s/mb' % self.wd
        self.paths['scripts_path']='%s/scripts' % self.wd
        
        if not 'img_path' in self.paths : self.paths['img_path'] = "v%03d/%s" % (int(self.version),'x'.join( map(str, self.res.values()) ) )

        if not self.combine_exr:

            self.paths['img_path'] +="/<RenderPass>/%s_<RenderLayer>_<RenderPass>_lnf_v%03d" % (self.envs['WORKSPACE'],self.version)
            self.paths['img_name'] ="<RenderPass>/%s_<RenderLayer>_<RenderPass>_lnf_v%03d" % (self.envs['WORKSPACE'],self.version)
        
        else:
            self.paths['img_path'] +="/%s_<RenderLayer>_lnf_v%03d" % (self.envs['WORKSPACE'],self.version)
            self.paths['img_name'] ="%s_lnf_v%03d" % (self.envs['WORKSPACE'],self.version)
            
        
        
    def createJobScript(self):
        ''' create the RIB gen script '''
        
        
        if not os.path.isdir(self.paths['scripts_path']):
            os.makedirs(self.paths['scripts_path'])
        
        args={'scenefile':self.scenefile,
        'maya':self.maya_version,
        'camera':self.camera,
        'WORKSPACE':self.envs['WORKSPACE'],
        'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
        'img_path':self.paths['img_path'],
        'out_dir':self.paths['out_dir'],
        'USER':self.user,
        'layer':self.layer,
        'cpus':self.cpus,
        'render_cmd':self.render_cmd,
        'width':self.res['width'],
        'height':self.res['height']}
        
        
        args['img_planes']='-iip'
        
        args['taskscript']='''
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
            args['taskscript']='''

s=%d
e=%d

echo START :: $s
echo END :: $e

#SLICES

sl=$SGE_TASK_ID
crop_s=`calc 1.0/%d*$sl-1.0/%d`
crop_e=`calc 1.0/%d*$sl`

echo SLICE :: $sl

export SLICE_PADDED=`printf "%%02d" $SGE_TASK_ID`


        ''' % (self.start, self.start,self.slices,self.slices,self.slices)      
        
            args['sliceing']='-reg $crop_s $crop_e 0 %d' % (self.res['height'])
                
        
        #Generate BASH script
        maya_mr_script = open(self.paths['scripts_path']+"/maya_mr.sh", 'w')
        
        maya_mr_script.write('''#!/bin/bash\n\

#
# Mentalray Render script for : %(scenefile)s
#   

#$ -S /bin/bash
#$ -j y

    
#simple calculator script
function calc {
    echo "scale=4; $1" | bc ;
}


unset SLICE
unset SLICE_PADDED

%(taskscript)s

export START=$s
export END=$e

export MAYA_APP_DIR=${TMPDIR}/maya;
export MAYA_VERSION=%(maya)s;
export MAYA_MAJOR_VERSION=%(maya)s;
export MAYA_LOCATION=$SOFTWARE/maya/$UNAME.$DIST.$ARCH/%(maya)s;

#set workspace

source ${SOFTWARE}/bluebolt/envset/workspace %(WORKSPACE_PATH)s

#
# Maya path setting
#

export PATH=$MAYA_LOCATION/bin:$PATH

echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo MAYA_VERSION::: $MAYA_VERSION
echo WORKSPACE_PATH=$WORKSPACE_PATH;

cmd="%(render_cmd)s -r mr -v 5 -rt $NSLOTS -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -fnc name.#.ext -of exr -pad 4 %(img_planes)s -rd %(out_dir)s -im %(img_path)s -rl %(layer)s -rp 1 -cam %(camera)s -x %(width)s -y %(height)s -s $s -e $e %(scenefile)s"
echo $cmd

function this_task(){

time $cmd

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task

''' % (args))

        maya_mr_script.close()  
            
        
        
        if self.frames != '%d-%d' % (self.start,self.end) and self.frames == '0-0':
            self.frames='%d-%d' % (self.start,self.end)
                
        self.scripts['render_script'] = {'script':maya_mr_script,
                    'type':2,
                    'options':' -l maya_mr=1 -tc %d' % (self.max_slots),
                    'name':'maya_mr',
                    'frames':'%s' % self.frames,
                    'step':self.step}

        self.script = maya_mr_script.name
        
        return self.script

    
    def makeScripts(self):
        ''' Generate the render scripts and the qsub submission script '''
        
        print 'generating scripts in ... %s' % self.wd
        
        #if self.publishscene:
                    
        if not os.path.isdir(self.paths['mb_path']):
            mkfolder(self.paths['mb_path'])       
        
        publishedfile="%s/%s" % (self.paths['mb_path'],os.path.basename(self.scenefile))
        
        if not os.path.isfile(publishedfile):
            print "Copying scene file ..."
            org_size=os.path.getsize(self.scenefile)
            copyFile(self.scenefile,self.paths['mb_path'])
        
        
        self.scenefile = publishedfile
        
        return self.createJobScript()

    def makeJobs(self):

        self.setPaths()

        self.makeScripts()
    
    
    def output(self):
        ''' Submit this job to gridengine '''
        
        
        output = "submitting job...: %s \n" % self.name
        output+= "working dir......: %s \n" % self.wd
        output+= "maya scene.......: %s \n" % self.scenefile
        output+= "version..........: %s \n" % self.version
        output+= "image dir........: %s \n" % self.paths['img_path']
        output+= "frames...........: %s \n" % self.frames
        output+= "step.............: %d \n" % int(self.step)
        output+= "camera...........: %s \n" % self.camera
        output+= "layer............: %s \n" % self.layer
        output+= "queue............: %s \n" % self.queue
        output+= "cpus.............: %s \n" % self.cpus
        output+= "renderpass.......: %s \n" % self.render_pass
        output+= "maya version.....: %s \n" % self.maya_version
        output+= "send disabled....: %s \n" % str(self.paused)
                
        return output