
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
	Main mkdaily class

''' 
from gridengine.Job import Job,JobType
from gridengine.Job import mkfolder

import os , shutil
import datetime

from subprocess import Popen,PIPE

class mkdailyJob(Job):
	''' mkdaily instance of gridengine submitting class '''
	
	def __init__(self):
		super(mkdailyJob, self).__init__()
		self.name='mkdaily_job'
		self.type='mkdaily'
		self.queue='mkdaily.q'
		self.mkdaily_version='3.0.1'
		
		#mkdaily args 
		
		self.art='ashley-r'	#artist name shotgun username
		self.dpx=False         	#create dpx slate and sequence
		self.dsc='comp'   	#discipline default "Comp"
		self.dt='bluebolt'	#'bluebolt' (internal) default or 'client'
		self.fmt='mov'		#output format: dpx exr jpg tif
		self.inf=''		#path to source images
		self.sn=''     		#slate note
		
		self.log=None        	#not used kept for compatability reasons
		self.of=None   		#base path to destination images,
		self.osf=None		#output start frame
		self.oef=None  		#output end frame
		self.scl=1.0         	#scale of something...
		self.slo=False       	#Don't render a slate
		self.ush=True  		#write to the database. Default: True
		self.ver=1		#version number e.g. 001
		
		self.vid=None          	#version id (shotgun version id ) e.g 1654 if this is set use 'get_mkdaily_cmd' instead
		
		self.vnm='new_version'  #version name
		self.t=False            #thumbnail only
		
		self.scripts={}
	
	def setJobName(self):
		'''
			Set the name of the job based on SHOT, daily Version and datetime stamp
		'''
		dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
		self.name='%s_v%03d.%s' % (self.envs['SHOT'],self.ver,dt)
		self.prefix='%s_v%03d' % (self.envs['SHOT'],self.ver)
	
		
	def createJobScript(self):
		'''
			Generate the job script for this submission to grid
		'''
		
		#construct the mkdaily command based on self.vid (versionid) being set
		
		cmd=''
		
		if not self.vid: #create the mkdaily command from the other arguments
			
			'''	
			self.art='ashley-r'	#artist name shotgun username
			self.dpx=False         	#create dpx slate and sequence
			self.dsc='comp'   	#discipline default "Comp"
			self.dt='bluebolt'	#'bluebolt' (internal) default or 'client'
			self.fmt='mov'		#output format: dpx exr jpg tif
			self.isf=1001 
			self.ief=1100
			self.if=''		#path to source images
			self.sn=''     		#slate note
			
			self.log=None        	#not used kept for compatability reasons
			self.of=None   		#base path to destination images,
			self.osf=None		#output start frame
			self.oef=None  		#output end frame
			self.scl=1           	#scale of something...
			self.slo=False       	#Don't render a slate
			self.ush=True  		#write to the database. Default: True
			self.ver=1		#version number e.g. 001
			
			self.vid=None          	#version id (shotgun version id ) e.g 1654 if this is set use 'get_mkdaily_cmd' instead
			
			self.vnm='new_version'  #version name
			self.t=False            #thumbnail only
			'''
			
			#set up the string flags
			
			if self.frames != '%d-%d' % (self.start,self.end) and self.frames == '0-0':
				self.frames='%d-%d' % (self.start,self.end)
				
			elif self.frames != '0-0':
				frames_split=self.frames.split(',')[0].split('-')
				
				if len(frames_split) == 2:
					self.start,self.end = frames_split
						
			framerange='--isf=%s --ief=%s' % (self.start,self.end)
			
			log_str=''
			if self.log!=None:
				log_str='--log=%s' % self.log
			
			of_str=''
			if self.of!=None:
				of_str='--of=%s' % self.of	
			
			ouframerange=''
			if self.osf != None and self.oef !=None:
				ouframerange='--osf=%s --oef=%s' % (self.osf,self.oef)
				
			scl_str=''
			if self.scl!=1.0:
				scl_str='--scl=%f' % self.scl
				
			t_str=''
			if self.t:
				t_str='-t'
			
			flags={'dt':self.dt,'dpx':self.dpx,'vnm':self.vnm,
			'ver':self.ver,'dsc':self.dsc,'inf':self.inf,
			'framerange':framerange,'art':self.art,'sn':self.sn,
			'log':log_str,'of':of_str,'outframerange':ouframerange,
			'scl':scl_str,'slo':self.slo,'ush':self.ush,'t':t_str}
			
			args = '--dt=%(dt)s --dpx=%(dpx)s --vnm=%(vnm)s --ver=%(ver)03d '\
			'--dsc=%(dsc)s --if=%(inf)s %(framerange)s --art=%(art)s --sn="%(sn)s"'\
			'%(log)s %(of)s %(outframerange)s %(scl)s --slo=%(slo)s --ush=%(ush)s %(t)s' % (flags)
			
			cmd='mkdaily %s' % args
		else:
			# generate command from get_mkdaily_cmd vid
			
			get_mkdaily_cmd_args={'client':'cl','bluebolt':''}
			md_args=['/software/wrappers/get_mkdaily_cmd',str(self.vid),get_mkdaily_cmd_args[self.dt]]
			
			if self.dpx:
				md_args.append('dpx')	
			
			cmd_bin= Popen(md_args,stdout=PIPE)
			cmd=cmd_bin.communicate()[0].strip()
			cmd_bin.stdout.close()
		
		
		settings={'mkdaily':self.mkdaily_version,
		'SHOW':self.envs['SHOW'],
		'SHOW_PATH':self.envs['SHOW_PATH'],
		'SCENE':self.envs['SCENE'],
		'SCENE_PATH':self.envs['SCENE_PATH'],
		'SHOT':self.envs['SHOT'],
		'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
		'cmd':cmd,
		'USER':self.user}

		if not os.path.isdir(self.wd):
			mkfolder(self.wd)
	
		f = open(self.wd+"/mkdaily."+self.name+".render", 'w')
		
		f.write('''#!/bin/bash
#$ -S /bin/bash
#$ -j y
umask 0002

#set workspace

source /software/bluebolt/envset/workspace %(WORKSPACE_PATH)s

export MKDAILY_VERSION=%(mkdaily)s
echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo MKDAILY_VERSION::: $MKDAILY_VERSION


cmd='%(cmd)s'

echo
echo $cmd
echo
exec $cmd

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus\n''' % (settings))
	
	
		f.close()


		# priorotize non development dailies over dev ones
		options=' -l mkdaily=1'

		if not self.envs['SHOW'].endswith('_dev'):
			options+='-p -100'
		
		self.scripts['render_script'] = {'script':f,'type':1,'options':options,'name':'mkdaily','frames':'%s' % self.frames,'step':self.step}
		
		return f
		
	
	def setWD(self,directory):	
		''' Set the working directory for this job, this is where the log output will be put'''
		
		self.wd=os.path.abspath(directory)
		self.paths['log_path']='%s/' % self.wd
			
	def makeScripts(self):
		''' Generate the render scripts'''
		j_scripts=list()
		j_scripts.append(self.createJobScript())
	
		return j_scripts
	
	
	def output(self):
		''' generate job infomation output '''
		
		
		output = "submitting job...: %s \n" % self.name
		output+= "working dir......: %s \n" % self.wd
		output+= "frames...........: %d-%d \n" % (int(self.start),int(self.end))
		output+= "step.............: %d \n" % int(self.step)
		output+= "mkdaily version..: %s \n" % self.mkdaily_version
		output+= "send disabled....: %s \n" % str(self.paused)
		output+= "update Shotgun...: %s \n" % str(self.ush)
				
		return output
	
