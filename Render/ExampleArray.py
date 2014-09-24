"""
(c)2011 Bluebolt Ltd.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
* Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following disclaimer
in the documentation and/or other materials provided with the
distribution.
* Neither the name of Bluebolt nor the names of
its contributors may be used to endorse or promote products derived
from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Author:Ashley Retallack - ashley-r@blue-bolt.com


"""

#################
#
#	Example of an array job class
#
################### 


from gridengine.Job import Job,JobType
from gridengine.Job import mkfolder

import os , shutil
import datetime


class ExampleArray(Job):

	''' Example instance of gridengine submitting class '''

	def __init__(self):
		# We need to take with us the attributes and 
		# commands from the defalt job class 
		super(ExampleArray, self).__init__() 
		self.name='my_job'
		self.type='myapp'
		self.myappversion='1.0' # defult app version to use
		self.queue='my.q'
		self.runcommand=''	
		self.scripts={} #this is a dict of the scripts that will get run

	
	def setJobName(self):
		''' Set the name of the job as it will appear in Grid engine '''
		dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
		self.name=os.path.basename(self.runcommand.strip('.ext'))+'.'+str(dt)
		self.prefix=os.path.basename(self.runcommand.strip('.ext'))



	def createJobScript(self):	
		'''
		Create a job script for an array task
		'''
		
		
		if self.frames != '%d-%d' % (self.start,self.end) and self.frames == '1-20':
			self.frames='%d-%d' % (self.start,self.end)
		
		
		settings={'runcommand':self.runcommand,
		'myappversion':self.myappversion,
		'SHOW':self.envs['SHOW'],
		'SHOW_PATH':self.envs['SHOW_PATH'],
		'SCENE':self.envs['SCENE'],
		'SCENE_PATH':self.envs['SCENE_PATH'],
		'SHOT':self.envs['SHOT'],
		'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
		'render_cmd':'/path/to/app',
		'USER':self.user}

		# cerate the working directory if it doesn't exit

		if not os.path.isdir(self.wd):
			mkfolder(self.wd)
	
		#open up the render script that will get executed and add the contents
			
		f = open(self.wd+"/myapp."+self.name+".render", 'w')
		
		f.write('''#!/bin/bash
#$ -S /bin/bash
#$ -j y
umask 0002

#set workspace

source ${SOFTWARE}/bluebolt/envset/workspace %(WORKSPACE_PATH)s

export MYAPP_VERSION=%(myappversion)s
echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo NUKE_VERSION::: $NUKE_VERSION

s=$SGE_TASK_ID
e=`echo $[$s+$SGE_TASK_STEPSIZE-1]`
if [ $e -ge $SGE_TASK_LAST ]; then
	e=$SGE_TASK_LAST;
fi

echo START :: $s
echo END :: $e

cmd="%(render_cmd)s -args ... -F $s-$e -x %(runcommand)s "

function this_task(){

echo
echo $cmd
echo
exec $cmd 
exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task\n''' % (settings))
	
	
		f.close()		
		
		# add this script to the render scripts dictionary

		'''
		'script' : script to executed
		'type' : 0 - redunant scripts (non-executable), 1 - single job, 2 - array job
		'name' : this job type name that will go at the start of this script
		-- optionals --
		'options' : any arguments that the submitter needs e.g resourses
		'frames' : a string containing the list of ranges to render in an array job
		'step' : the step size for the tasks in an array job
		'dep' : the 'name'(above) of the script this job script depends on 
			 and will wait to be completed before atrting
		'''

		self.scripts['render_script'] =  {'script':f,'type':2,'options':' -l myapp=1 -tc 15 ','name':'myapp','frames':'%s' % self.frames,'step':self.step}
		
		return f


	
	def makeScripts(self):		
		''' Generate the render scripts '''
		outscripts=list()
		
		outscripts.append(self.createRenderScript())
	
		return outscripts
	
		
	def output(self):
		''' Return a string of stats about this job submission '''		
		
		# extra_data will be placed in to the sql database for
		# gathering of info later and statistic analysis 
		self.extra_data={
			'runcommand':self.runcommand,
			'myappversion':self.myappversion,
			'frames':self.frames,
		}
		
		
		output = "submitting job...: %s \n" % self.name
		output+= "working dir......: %s \n" % self.wd
		output+= "runcommand.......: %s \n" % self.runcommand
		output+= "frames...........: %s \n" % self.frames
		output+= "step.............: %d \n" % int(self.step)
		output+= "queue............: %s \n" % self.queue
		output+= "myapp version.....: %s \n" % self.myappversion
		output+= "send disabled....: %s \n" % str(self.paused)
				
		return output
		
	
