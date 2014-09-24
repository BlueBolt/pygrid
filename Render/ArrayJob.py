
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
from gridengine.Job import Job,JobType
from gridengine.Job import mkfolder

import os , shutil
import datetime

from subprocess import Popen,PIPE

class ArrayJob(Job):
	''' mkdaily instance of gridengine submitting class '''
	
	def __init__(self):
		super(ArrayJob, self).__init__()
		self.name = 'command_job'
		self.type = 'command'
		self.queue = 'all.q'
		self.envs = {}
		self.prescript = ""
		self.taskscript = """
s=$SGE_TASK_ID
e=`echo $[$s+$SGE_TASK_STEPSIZE-1]`
if [ $e -ge $SGE_TASK_LAST ]; then
	e=$SGE_TASK_LAST;
fi
"""
		
		#command args 
		self.cmd='ls -la'
	
	def setJobName(self):
		'''
			Set the name of the job based on SHOT, daily Version and datetime stamp
		'''
		dt = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
		self.name='cmd.%s.%s' % (self.cmd.split()[0],dt)
	
		
	def createJobScript(self):
		'''
			Generate the job script for this submission to grid
		'''
		
		envs = ""
		
		for e in self.envs.keys():
			envs += "export %s=%s" % (e,self.envs[e])
		
		settings={'cmd':self.cmd,'envs':envs,'prescript':self.prescript}

		if not os.path.isdir(self.wd):
			mkfolder(self.wd)
	
		f = open(self.wd+"/mkdaily."+self.name+".render", 'w')
		
		f.write('''#!/bin/bash
#$ -S /bin/bash
#$ -j y
umask 0002

%(prescript)s

%(envs)s

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

		self.scripts['cmd_script'] = {'script':f,'type':1,'name':'cmd'}
		
		return f
		
	
	def setWD(self,directory):
		''' Set the working directory for this job, this is where the log output will be put'''
		
		self.wd=os.path.abspath(directory)
		self.paths['log_path']='%s/logs' % self.wd	
		
		

	def createQsubExecScript(self):
		''' 
			create the qsub submission script.
		'''
		
		
		exe="qsub -r y"
		
		if self.paused:
			exe+=" -h "
			
		args={'email':'-m a -M %s@blue-bolt.com' % os.getenv('USER'),
		'jobname':self.name,
		'wd':self.wd,
		'render_script':self.scripts['render_script']['script'].name,
		'logs_path':self.paths['log_path'],
		'exe':exe,
		'CPUS':self.cpus}
					
		# Make logs directory
		
		if not os.path.isdir(self.paths['log_path']):
			mkfolder(self.paths['log_path'])
			
		
		
		script = '''#!/bin/bash
#
# Submision Script for %s
#			\n''' % (self.scenefile)
		
		
		if not self.email:
			args['email']=''
		
		script+="%(exe)s -l mem_free=4G  %(email)s -N %(jobname)s -o %(logs_path)s -wd %(wd)s %(render_script)s;\n" % (args)
		
		
		f = open(self.paths['scripts_path']+"/"+args['jobname'], 'w')
		f.write(script)
		f.close()
	
		os.chmod(self.paths['scripts_path']+"/"+args['jobname'], 0775)
		
		# assign this script to the main script name
		
		self.script=f
		
		return f
			
	def makeScripts(self):
		''' Generate the render scripts'''
		j_scripts=list()
		j_scripts.append(self.createJobScript())
		j_scripts.append(self.createQsubExecScript())
	
		return j_scripts
	
	
	def output(self):
		''' generate job infomation output '''
		
		
		output = "submitting job...: %s \n" % self.name
		output+= "command..........: %s \n" % self.cmd
		output+= "working dir......: %s \n" % self.wd
		output+= "send disabled....: %s \n" % str(self.paused)
				
		return output
	
