
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
	Main Maya Software Render class

	has one job:
	 
	 render_mr -- do the render

''' 
from gridengine.Job import Job,JobType
from gridengine.Job import mkfolder
import os , shutil
import datetime

class mayaSWJob(Job):
	''' 3delight instance of gridengine submitting class '''
	
	def __init__(self):
		super(mayaSWJob, self).__init__()	
		self.name='Maya_sw_job'
		self.type='maya_sw'
		self.queue='3d.q'
		self.cleanup=False
		self.seqcheck=False
		self.combine_exr=False
		self.publishscene=False
		self.cpus=2
		self.scenefile=''
		self.resources={'mem_free':'4G','maya':self.cpus}
		self.mayaversion='2011'
		self.layer='defaultRenderLayer'
		self.bake_layer='defaultRenderLayer'
		self.render_pass=''
		self.camera='perspShape'
		self.version=1
		self.res={'width':'2048','height':'1556'}
		self.slices=0
		self.render_cmd='Render'
		self.prefix=''
		self.scripts={}
		
	
	def setversion(self):
		''' check and set the version based on the render_tmp location '''
		
		if self.paths.has_key('out_dir'):
			self.version = 1
			if os.path.isdir(self.paths['pass_path']):				
				dirlist=os.listdir(self.paths['pass_path'])
				dirlist.sort()
				for d in  dirlist:
					self.version = int(d.strip('v').strip("_published"))+1	
			
			self.setWD('%s/%s/%s/v%03d' % (self.paths['pantry'],self.layer,self.render_pass,self.version))
			
		
		
	def setJobName(self):
		dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
		self.name=os.path.basename(self.scenefile.strip('.mb').strip('.ma'))+"_"+self.layer+"_"+self.render_pass+'.'+str(dt)
		self.prefix=os.path.basename(self.scenefile.strip('.mb').strip('.ma'))+"_"+self.layer+"_"+self.render_pass
		
	def setPaths(self):
		''' Set the paths for pantry based resources (tdls,sdls,shadowmaps) '''
		
		self.paths['out_dir']=''
		
		if '3d_builds' in os.path.abspath(self.envs['WORKSPACE_PATH']):
			self.paths['out_dir']="%s/render_tmp/" % (self.envs['WORKSPACE_PATH'])
		else:
			self.paths['out_dir']="%s/3d/render_tmp/" % (self.envs['WORKSPACE_PATH'])
		
		self.paths['pantry']='%(SHOW_PATH)s/3d/pantry/%(SHOT)s' % (self.envs)
		
		self.paths['pass_path']='%s/%s/%s' % (self.paths['out_dir'],self.layer,self.render_pass)
				
		self.setversion()
		
		os.makedirs("%s/v%03d" % (self.paths['pass_path'],self.version))
		
		self.paths['mb_path']='%s/mb' % self.wd
		self.paths['scripts_path']='%s/scripts' % self.wd
		
		if not self.combine_exr:
				
			self.paths['img_path'] ="<RenderLayer>/%s/v%03d/%s/<RenderPass>/%s_<RenderPass>_v%03d" % (self.render_pass,self.version,'x'.join(self.res.values()),self.envs['SHOT'],self.version)
			self.paths['img_name'] ="<RenderPass>/%s_<RenderPass>_v%03d" % (self.envs['SHOT'],self.version)
		
		else:
			self.paths['img_path'] ="<RenderLayer>/%s/v%03d/%s/%s_v%03d" % (self.render_pass,self.version,'x'.join(self.res.values()),self.envs['SHOT'],self.version)
			self.paths['img_name'] ="%s_v%03d" % (self.envs['SHOT'],self.version)
			
		
		
	def createJobScript(self):
		''' create the RIB gen script '''
		
		
		if not os.path.isdir(self.paths['scripts_path']):
			os.makedirs(self.paths['scripts_path'])
		
		args={'scenefile':self.scenefile,
		'maya':self.mayaversion,
		'camera':self.camera,
		'SHOW':self.envs['SHOW'],
		'SHOW_PATH':self.envs['SHOW_PATH'],
		'SCENE':self.envs['SCENE'],
		'SCENE_PATH':self.envs['SCENE_PATH'],
		'SHOT':self.envs['SHOT'],
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
		maya_sw_script = open(self.paths['scripts_path']+"/maya_sw.sh", 'w')
		
		maya_sw_script.write('''#!/bin/bash\n\

#
# RIB Generation script for : %(scenefile)s
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

###################################
# END STUBS FOR MAYA SEARCH PATHS #
###################################

export MAYA_SHELVES=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_MAJOR_VERSION/shelves

export MAYA_SCRIPTS=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_MAJOR_VERSION/scripts

export MAYA_MODULES=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_MAJOR_VERSION/modules

export MAYA_PLUG_INS=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_MAJOR_VERSION/plugins

##################################
# COMPANY WIDE MAYA SEARCH PATHS #
##################################

export MAYA_SHELF_PATH=$HOME/$MAYA_SHELVES:$WORKSPACE_PATH/$MAYA_SHELVES:$SCENE_PATH/$MAYA_SHELVES:$SHOW_PATH/$MAYA_SHELVES:/software/$MAYA_SHELVES:/software/bluebolt/$MAYA_SHELVES

export MAYA_SCRIPT_PATH=$HOME/$MAYA_SCRIPTS:$WORKSPACE_PATH/$MAYA_SCRIPTS:$SCENE_PATH/$MAYA_SCRIPTS:$SHOW_PATH/$MAYA_SCRIPTS:/software/$MAYA_SCRIPTS:/software/bluebolt/$MAYA_SCRIPTS

export MAYA_MODULE_PATH=$HOME/$MAYA_MODULES:$WORKSPACE_PATH/$MAYA_MODULES:$SCENE_PATH/$MAYA_MODULES:$SHOW_PATH/$MAYA_MODULES:/software/$MAYA_MODULES:/software/bluebolt/$MAYA_MODULES

export MAYA_PLUG_IN_PATH=$HOME/$MAYA_PLUG_INS:$WORKSPACE_PATH/$MAYA_PLUG_INS:$SCENE_PATH/$MAYA_PLUG_INS:$SHOW_PATH/$MAYA_PLUG_INS:/software/$MAYA_PLUG_INS:/software/bluebolt/$MAYA_PLUG_INS

echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo DELIGHT_VERSION::: $DELIGHT_VERSION
echo WORKSPACE_PATH=$WORKSPACE_PATH;

cmd="%(render_cmd)s -r sw -n %(cpus)d -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -fnc \\\"name.#.ext\\\" -of tif -pad 4 %(img_planes)s -rd \\\"%(out_dir)s\\\" -im \\\"%(img_path)s\\\" -rl %(layer)s -rp 1 -cam %(camera)s -x %(width)s -y %(height)s -s $s -e $e %(scenefile)s"
echo $cmd

function this_task(){

%(render_cmd)s -r sw -n %(cpus)d -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -fnc \"name.#.ext\" -of tif -pad 4 %(img_planes)s -rd "%(out_dir)s" -im "%(img_path)s" -rl %(layer)s -rp 1 -cam %(camera)s -x %(width)s -y %(height)s -s $s -e $e %(scenefile)s

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task

''' % (args))

		maya_sw_script.close()	
			
		
		
		if self.frames != '%d-%d' % (self.start,self.end) and self.frames == '1-20':
			self.frames='%d-%d' % (self.start,self.end)
				
		self.scripts['render_script'] = {'script':maya_sw_script,
					'type':2,
					'options':' -l maya_sw=%s -tc 50 ' % (self.cpus),
					'name':'maya_sw',
					'frames':'%s' % self.frames,
					'step':self.step}
		
		return maya_sw_script
		
	def createQsubExecScript(self):
		
		
		exe="qsub -r y"
		
		if self.paused:
			exe+=" -h "
				
			
		args={'framerange':'%d-%d' % (self.start,self.end),
		'step':self.step,
		'email':'-m a -M %s@blue-bolt.com' % os.getenv('USER'),
		'jobname':self.name,
		'wd':self.wd,
		'script':self.scripts['render_script']['script'].name,
		'logs':self.paths['log_path'],
		'exe':exe,
		'cpu':self.cpus}
				
		# Make logs directory
		
		if not os.path.isdir(self.paths['log_path']):
			mkfolder(self.paths['log_path'])
	
		if not self.email:
			args['email']=''
	
		script = '''#!/bin/bash
#
# Submision Script for %s
#			\n''' % (self.scenefile)


		script+="%(exe)s -l mem_free=4G -l maya_sw=%(cpu)s -q 3d.q -t %(framerange)s:%(step)s %(email)s -tc 50 -N maya_sw.%(jobname)s -wd %(wd)s -o %(logs)s %(script)s\n" % args
		
		f = open(self.paths['scripts_path']+"/"+self.name, 'w')
		f.write(script)
		f.close()
	
		os.chmod(self.paths['scripts_path']+"/"+self.name, 0775)	
		
		self.script=f
		
		return self.script
	
	
	def makeScripts(self):
		''' Generate the render scripts and the qsub submission script '''
		
		print 'generating scripts in ... %s' % self.wd
		
		#if self.publishscene:
			
		mb_path = "%s/mb/" % (self.wd)
		
		if not os.path.isdir(mb_path):
			mkfolder(mb_path)		
		
		publishedfile="%s/%s" % (mb_path,os.path.basename(self.scenefile))
		
		if not os.path.isfile(publishedfile):
			print "Copying scene file ..."
			org_size=os.path.getsize(self.scenefile)
			shutil.copyfile(self.scenefile,publishedfile)
		
		
		self.scenefile = publishedfile
		
		self.createJobScript()
		self.createQsubExecScript()
	
		return self.createQsubExecScript()
	
	
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
		output+= "maya version.....: %s \n" % self.mayaversion
		output+= "send disabled....: %s \n" % str(self.paused)
				
		return output