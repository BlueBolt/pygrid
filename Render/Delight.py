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
Created:2011-06-07
Version:0.9.82
"""

#################
#
#	Main 3delight class
#
#	has three dependent jobs:
#	 
#	 preflight -- shadowmaps,ptc...
#	 ribgen -- generate the ribfilesfrom maya
#	 renderdl -- do the render
#
#	TODO 
#
#	delight v 9.0.116+ has merged exr built in
#	
#
#
#	postscript -job
#	mysql updating on:
#	 	creation of job
#		individual task completion
#		job statistics
#
################### 

from gridengine.Job import Job,JobType
from gridengine.Job import mkfolder
import os , shutil

maya_stub = '''
###################################
# END STUBS FOR MAYA SEARCH PATHS #
###################################

export MAYA_SHELVES=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_VERSION/shelves

export MAYA_SCRIPTS=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_VERSION/scripts

export MAYA_MODULES=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_VERSION/modules

export MAYA_PLUG_INS=tools/maya/$UNAME.$DIST.$ARCH/$MAYA_VERSION/plug-ins

##################################
# COMPANY WIDE MAYA SEARCH PATHS #
##################################

export MAYA_SHELF_PATH=$HOME/$MAYA_SHELVES:$WORKSPACE_PATH/$MAYA_SHELVES:$SCENE_PATH/$MAYA_SHELVES:$SHOW_PATH/$MAYA_SHELVES:/software/$MAYA_SHELVES:/software/bluebolt/$MAYA_SHELVES

export MAYA_SCRIPT_PATH=$HOME/$MAYA_SCRIPTS:$WORKSPACE_PATH/$MAYA_SCRIPTS:$SCENE_PATH/$MAYA_SCRIPTS:$SHOW_PATH/$MAYA_SCRIPTS:/software/$MAYA_SCRIPTS:/software/bluebolt/$MAYA_SCRIPTS

export MAYA_MODULE_PATH=$HOME/$MAYA_MODULES:$WORKSPACE_PATH/$MAYA_MODULES:$SCENE_PATH/$MAYA_MODULES:$SHOW_PATH/$MAYA_MODULES:/software/$MAYA_MODULES:/software/bluebolt/$MAYA_MODULES

export MAYA_PLUG_IN_PATH=$HOME/$MAYA_PLUG_INS:$WORKSPACE_PATH/$MAYA_PLUG_INS:$SCENE_PATH/$MAYA_PLUG_INS:$SHOW_PATH/$MAYA_PLUG_INS:/software/$MAYA_PLUG_INS:/software/bluebolt/$MAYA_PLUG_INS

'''


class DelightJob(Job):
	''' 3delight instance of gridengine submitting class '''
	
	def __init__(self):
		super(DelightJob, self).__init__()
		self.name='delight_job'
		self.type='delight'
		self.preflight=False
		self.queue='3d.q'
		self.bake=False
		self.stats=True
		self.cleanup=False
		self.seqcheck=False
		self.combineEXR=False
		self.publishscene=False
		self.netcache_enable=True
		self.netcache_size=524288
		self.netcache_dir='/disk1/tmp/3delight'
		self.scenefile=''
		self.resources={'mem_free':'4G','dl':self.cpus}
		self.delightversion='10.0.29'
		self.mayaversion='2012'
		self.layer='defaultRenderLayer'
		self.bake_layer='defaultRenderLayer'
		self.render_pass=''
		self.shader_collection='<none>'
		self.shader_collection_str=''
		self.camera='perspShape'
		self.version=1
		self.resmult=0
		self.res={'width':'1920','height':'1080'}
		self.slices=0
		self.aovs={'beauty':{'aovs':['rgba'],'half_float':True,'premult':True}}
		self.render_cmd='Render'
		self.prefix=''
		self.scripts={}
		self.outFrames=""
		self.use_showAOVS=False
		
		
		
	
	def setversion(self):
		''' check and set the version based on the render_tmp location '''
		
		if self.paths.has_key('out_dir'):
			self.version = 1
			if os.path.isdir(self.paths['out_dir']):
				dirlist=os.listdir(self.paths['out_dir'])
				dirlist.sort()
				for d in  dirlist:
					self.version = int(d.strip('v').strip("_published"))+1	
	
			self.setVersionWD()
	
	def setVersionWD(self):
		''' set the working directory based on the version given'''
		
		self.setWD('%s/%s/%s/%s/v%03d' % (self.paths['pantry'],
											self.camera.split(':')[-1],
											self.layer,
											self.render_pass,
											self.version))
			
		
		
	def setJobName(self):
		dt=self.dt.strftime('%Y%m%d%H%M%S')
		self.name=os.path.basename(self.scenefile.strip('.mb').strip('.ma'))+"_"+self.layer+"_"+self.render_pass+'.'+str(dt)
		self.prefix=os.path.basename(self.scenefile.strip('.mb').strip('.ma'))+"_"+self.layer+"_"+self.render_pass
		
	def addAOV(self,aov):
		self.aovs.append(aov)
			
	def setPaths(self):
		''' Set the paths for pantry based resources (tdls,sdls,shadowmaps) '''
		
		self.paths['out_dir']=''
		
		if '3d_builds' in os.path.abspath(self.envs['WORKSPACE_PATH']):
			self.paths['out_dir']="%s/render_tmp/%s/%s/%s/" % (self.envs['WORKSPACE_PATH'],self.camera.split(':')[-1],self.layer,self.render_pass)
		else:
			self.paths['out_dir']="%s/3d/render_tmp/%s/%s/%s/" % (self.envs['WORKSPACE_PATH'],self.camera.split(':')[-1],self.layer,self.render_pass)
		
		self.paths['pantry']='%(SHOW_PATH)s/3d/pantry/%(SHOT)s' % (self.envs)
				
		self.setversion()
		
		os.makedirs("%s/v%03d" % (self.paths['out_dir'],self.version))
		
		self.paths['mb_path']='%s/mb' % self.wd
		self.paths['rib_path']='%s/rib' % self.wd
		self.paths['sdl_path']='%s/shaders' % self.wd
		self.paths['tdl_path']='%s/textures' % self.wd
		self.paths['ptc_path']='%s/ptc' % self.wd
		self.paths['shad_path']='%s/shadows' % self.wd
		
		self.paths['img_path'] ="%s/v%03d/%s/<output_variable>/%s_lnh_<output_variable>_v%03d" % (self.paths['out_dir'],self.version,'x'.join(self.res.values()),self.envs['SHOT'],self.version)
		
		
	def createPreflightJobScript(self):
		''' Generate the shell script that the PREFLIGHT job will use, 		
			this is the first job to be sent to the grid '''
		
		# TODO check that paths is set if not set it #
		
		# make scripts path if it doesn't exists #
		
		if not os.path.isdir(self.paths['scripts_path']):
			os.makedirs(self.paths['scripts_path'])
		
		# settings #
		
		settings={'scenefile':self.scenefile,
		'wd':self.wd,
		'delight':self.delightversion,
		'maya':self.mayaversion,
		'maya_stub':maya_stub,
		'SHOW':self.envs['SHOW'],
		'SHOW_PATH':self.envs['SHOW_PATH'],
		'SCENE':self.envs['SCENE'],
		'SCENE_PATH':self.envs['SCENE_PATH'],
		'SHOT':self.envs['SHOT'],
		'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
		'camera':self.camera,
		'sdl_path':self.paths['sdl_path'],
		'tdl_path':self.paths['tdl_path'],
		'shad_path':self.paths['shad_path'],
		'render_cmd':self.render_cmd,
		'USER':self.user,
		'layer':self.layer,
		'render_pass':self.render_pass,
		'shader_collection':self.shader_collection_str,
		'slice':self.slices>1,
		'num_slices':self.slices,
		'resmult':self.resmult,
		'CPUS':self.cpus}
	
		
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

			''' % (self.start, self.start)
			
		settings['bakepass']='' 
			
		if self.bake:
			settings['bakepass']='''Render -r 3delight -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -cpus %(CPUS)s -resm %(resmult)d -verb -arwm 1 -lr %(layer)s -rp BAKE_PASS %(shader_collection)s -cam %(camera)s -rmode 0 -is false -an 1 -s $s -e $e -rpd 0 -rsd 0 -rsm 0 -prog 1 -statl 3 %(scenefile)s''' 
	
		
	
		#Generate preflight BASH script
		preflight_bash_script = open(self.paths['scripts_path']+"/preflight.sh", 'w')
		
		preflight_bash_script.write('''#!/bin/bash
		
#
# Preflight task for : %(scenefile)s
#	


#$ -S /bin/bash
#$ -j y

umask 0002

#set workspace

source ${SOFTWARE}/bluebolt/envset/workspace %(WORKSPACE_PATH)s

export MAYA_APP_DIR=${TMPDIR}/maya;

export DELIGHT_VERSION=%(delight)s;
export MAYA_VERSION=%(maya)s;
export MAYA_MAJOR_VERSION=%(maya)s;
export MAYA_LOCATION=$SOFTWARE/maya/$UNAME.$DIST.$ARCH/%(maya)s;

echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo DELIGHT_VERSION::: $DELIGHT_VERSION
echo WORKSPACE_PATH=$WORKSPACE_PATH;

%(taskscript)s

unset DL_SHADERS_PATH
unset DL_DISPLAYS_PATH
unset DL_TEXTURES_PATH

mkdir -p %(sdl_path)s/$s
export _3DFM_OUTPUT_PATH=%(wd)s;
export _3DFM_SHADERS_PATH=%(sdl_path)s/$s;
export _3DFM_TEXTURES_PATH=%(tdl_path)s;
export _3DFM_SHADOWMAPS_PATH=%(shad_path)s;

cmd="%(render_cmd)s -r 3delight -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -cpus %(CPUS)s -resm %(resmult)d -verb -arwm 1 -lr %(layer)s -rp %(render_pass)s %(shader_collection)s -cam %(camera)s -rmode 0 -is false -an 1 -s $s -e $e -rpd 0 -rsd 0 -rsm 1 -sssm 1 -prog 1 -statl 3 %(scenefile)s;"
echo $cmd
#Run it
function this_task(){

time %(render_cmd)s -r 3delight -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -cpus %(CPUS)s -resm %(resmult)d -verb -arwm 1 -lr %(layer)s -rp %(render_pass)s %(shader_collection)s -cam %(camera)s -rmode 0 -is false -an 1 -s $s -e $e -rpd 0 -rsd 0 -rsm 1 -sssm 1 -prog 1 -statl 3 %(scenefile)s;

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task

''' % (settings))
		
		preflight_bash_script.close()
		
		return preflight_bash_script
				
	def createBakeJobScript(self):
		''' Generate the shell script that the PREFLIGHT job will use, 		
			this is the first job to be sent to the grid '''
				
		# make scripts path if it doesn't exists #
		
		if not os.path.isdir(self.paths['scripts_path']):
			os.makedirs(self.paths['scripts_path'])
		
		# settings #
		
		settings={'scenefile':self.scenefile,
		'wd':self.wd,
		'delight':self.delightversion,
		'maya':self.mayaversion,
		'maya_stub':maya_stub,
		'SHOW':self.envs['SHOW'],
		'SHOW_PATH':self.envs['SHOW_PATH'],
		'SCENE':self.envs['SCENE'],
		'SCENE_PATH':self.envs['SCENE_PATH'],
		'SHOT':self.envs['SHOT'],
		'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
		'camera':self.camera,
		'sdl_path':self.paths['sdl_path'],
		'tdl_path':self.paths['tdl_path'],
		'shad_path':self.paths['shad_path'],
		'render_cmd':self.render_cmd,
		'USER':self.user,
		'layer':self.layer,
		'bake_layer':self.bake_layer,
		'render_pass':self.render_pass,
		'shader_collection':self.shader_collection_str,
		'slice':self.slices>1,
		'num_slices':self.slices,
		'resmult':self.resmult,
		'CPUS':self.cpus}
	
		
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

			''' % (self.start, self.start)
	
		
	
		#Generate preflight BASH script
		bake_bash_script = open(self.paths['scripts_path']+"/bake.sh", 'w')
		
		bake_bash_script.write('''#!/bin/bash
		
#
# Bake task for : %(scenefile)s
#	


#$ -S /bin/bash
#$ -j y

umask 0002

#set workspace

source ${SOFTWARE}/bluebolt/envset/workspace %(WORKSPACE_PATH)s

export MAYA_APP_DIR=${TMPDIR}/maya;

export DELIGHT_VERSION=%(delight)s;
export MAYA_VERSION=%(maya)s;
export MAYA_MAJOR_VERSION=%(maya)s;
export MAYA_LOCATION=$SOFTWARE/maya/$UNAME.$DIST.$ARCH/%(maya)s;

#
# Maya path setting
#

export PATH=${SOFTWARE}/maya/$UNAME.$DIST.$ARCH/$MAYA_VERSION/bin:$PATH

export SHOW=%(SHOW)s;
export SHOW_PATH=%(SHOW_PATH)s;
export SCENE=%(SCENE)s;
export SCENE_PATH=%(SCENE_PATH)s;
export SHOT=%(SHOT)s;
export WORKSPACE_PATH=%(WORKSPACE_PATH)s;

mkdir -p %(sdl_path)s/$s
export _3DFM_OUTPUT_PATH=%(wd)s;
export _3DFM_SHADERS_PATH=%(sdl_path)s/$s;
export _3DFM_TEXTURES_PATH=%(tdl_path)s;
export _3DFM_SHADOWMAPS_PATH=%(shad_path)s;
source /software/bluebolt/config/delight.env;

echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo DELIGHT_VERSION::: $DELIGHT_VERSION
echo WORKSPACE_PATH=$WORKSPACE_PATH;

%(taskscript)s

cmd="%(render_cmd)s -r 3delight -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -cpus %(CPUS)s -resm %(resmult)d -verb -arwm 1 -lr %(bake_layer)s -rp BAKE_PASS %(shader_collection)s -cam %(camera)s -rmode 0 -is false -an 1 -s $s -e $e  -rpd 1 -of null -rsd 0 -rsm 0 -prog 1 -statl 3 %(scenefile)s"

function this_task(){

echo $cmd

exec $cmd

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task

''' % (settings))
		
		bake_bash_script.close()
		
		return bake_bash_script
		
	
	def createAOVMelScript(self):
		''' Create the MEL script that will set up the aovs for the render '''
				
		# make scripts path if it doesn't exists #
		
		if not os.path.isdir(self.paths['scripts_path']):
			mkfolder(self.paths['scripts_path'])
			
					
		outputPath = "%s" % (self.paths['img_path'])
		
		self.res_path="%s/v%03d/%s" % (self.paths['out_dir'],
								self.version,
								'x'.join(self.res.values()))
		
		args={'width':self.res['width'],
		'height':self.res['height'],
		'rib_path':'%s/%s_' % (self.paths['rib_path'],self.prefix),
		'img_path':self.paths['img_path'],
		'aov_str':'',
		'netcache_dir':self.netcache_dir,
		'netcache_size':self.netcache_size}
		
		
		if not os.path.isdir(self.paths['scripts_path']):
			mkfolder(self.paths['scripts_path'])
		
		padded_version = "v%03d" % self.version
		
		'''	
		aovs_list = dict()
				
		print self.aovs
		for output in self.aovs.keys():
			print output
			if output == "":
				continue
			else :
				for aov in self.aovs[output]['aovs']:
					print aov
					if aov == "":
						continue
					else:
						aovs_list[output].append(aov)
		
		
		aov_string='","'.join(aovs_list)
		'''
#		
#		aov_array_s = 'string $aovs[]={"%s"};\n' % aov_string
#		
#		aov_cmd=aov_array_s
		
		aov_cmd='''	
// 
//
//'''
		
		'''
		#	Set the old ones to the correct path and file type (even if they arn't renderable)		
		'''
				
		#self.delight_major_version=float('%s.%s' % (self.delightversion.split('.')[0],self.delightversion.split('.')[1]))
		#self.delight_build_version=float(self.delightversion.split('.')[2])
		
		args['i_output']=0
		
		args['aov_str']=''
		
		for output in self.aovs.keys():
		
			self.paths['img_path'] ="%s/v%03d/%s/%s/%s_%s_lnf_v%03d" % (self.paths['out_dir'],
														self.version,
														'x'.join(self.res.values()),
														output.lower(),
														self.envs['SHOT'],
														self.layer,
														self.version)
			
			
			args['img_path']=self.paths['img_path']
			args['aov_string']=','.join(self.aovs[output]['aovs'])
			args['output']=output
			
			if self.aovs[output].has_key('half_float'):
				args['half']=int(self.aovs[output]['half_float'])
			else:
				args['half']=1
				
			if self.aovs[output].has_key('premult'):
				args['premult']=int(self.aovs[output]['half_float'])
			else:
				args['premult']=1
				
			
			args['aov_str']+='''	
	print ("Adding : \\"%(output)s\\"\\n");
	setAttr -type "string" ($render_pass+".displayOutputVariables[%(i_output)d]") "%(aov_string)s";
	setAttr -type "string" ($render_pass+".displayDrivers[%(i_output)d]") "exr";
	setAttr -type "string" ($render_pass+".displayFilenames[%(i_output)d]") ("%(img_path)s"+$slice_str+".#.<ext>");
	setAttr ($render_pass+".displayQuantizeZeros[%(i_output)d]") 0;
	setAttr ($render_pass+".displayQuantizeOnes[%(i_output)d]") 0;
	setAttr ($render_pass+".displayQuantizeMins[%(i_output)d]") 0;
	setAttr ($render_pass+".displayQuantizeMaxs[%(i_output)d]") 0;
	setAttr ($render_pass+".displayQuantizeDithers[%(i_output)d]") 0;
	setAttr ($render_pass+".displayHalfFloats[%(i_output)d]") %(half)d;	
	setAttr ($render_pass+".displayRenderables[%(i_output)d]") 1;
	setAttr ($render_pass+".displayAssociateAlphas[%(i_output)d]") %(premult)d;
			''' % (args)
			
			
			# check if we have edgedetection involved
			# if so add the edge detection to it
			
			if self.aovs[output].has_key('edge_detection'):
				ed_EdgeVar=self.aovs[output]['edge_detection']
				
				edge_args={'ed_EdgeVar':ed_EdgeVar,'i_output':args['i_output']}
				
				args['aov_str']+='''
	setAttr -type "string" ($render_pass+".displayEdgeVarNames[%(i_output)d]") "%(ed_EdgeVar)s";
	setAttr ($render_pass+".displayEdgeEnables[%(i_output)d]") 1;
	setAttr ($render_pass+".displayEdgeColors[%(i_output)d]") -type double3 1 1 1 ;
	setAttr ($render_pass+".displayEdgeFilterWidths[%(i_output)d]") 1;
	''' % edge_args 
	
			else:
				args['aov_str']+='''
	setAttr ($render_pass+".displayEdgeEnables[%(i_output)d]") 0;
	''' % args
				
				
			args['i_output'] += 1
		
		aov_cmd+='''
	
//import pymel.core
python("from pymel.core import *");

//Set the resolution	

setAttr ($render_pass+".connectToRenderGlobals") 0;

if (python("PyNode('"+$render_pass+".resolutionX').isLocked()"))
	python("PyNode('"+$render_pass+".resolutionX').unlock()");
	
if (python("PyNode('"+$render_pass+".resolutionX').isConnected()"))
	python("PyNode('"+$render_pass+".resolutionX').disconnect()");
	

if (python("PyNode('"+$render_pass+".resolutionY').isLocked()"))
	python("PyNode('"+$render_pass+".resolutionY').unlock()");
	
if (python("PyNode('"+$render_pass+".resolutionY').isConnected()"))
	python("PyNode('"+$render_pass+".resolutionY').disconnect()");
	
setAttr ($render_pass+".resolutionX") %(width)s;
setAttr ($render_pass+".resolutionY") %(height)s;
''' % args

		if self.netcache_enable:
			aov_cmd+='''

// Set up Net Cache

setAttr ($render_pass+".useNetCache") 1;
setAttr -type "string" ($render_pass+".netCacheDir") "%(netcache_dir)s";
setAttr ($render_pass+".netCacheSize") %(netcache_size)d;

''' % args

		aov_cmd+='''
// detect slicing

$slice=getenv("SLICE");

string $slice_str;

if ($slice != ""){
	
	

	$slice_str = "_$SLICE_PADDED";
	print($slice_str+"\\n");
}


$start = getenv("START");
$end = getenv("END");

// set the riboutput path 

setAttr -type "string" ($render_pass+".ribFilename") ("%(rib_path)s"+$start+"-"+$end+$slice_str+".rib");

// set secondarys on 
setAttr ($render_pass+".renderSecondaryDisplays") 1;

$numDisplays=`getAttr -s ($render_pass+".displayDrivers")`;
for ($d=0;$d<$numDisplays;$d++)
{
	setAttr ($render_pass+\".displayRenderables["+$d+"]") 0;
}
print ($render_pass+"\\n");
%(aov_str)s''' % (args)
		
		
		
		
		mel_script_fn = "%s/%s_aov.mel" % (self.paths['scripts_path'],self.prefix)
		
		mel_script = file(mel_script_fn,'w')
		mel_script.write(aov_cmd)
		mel_script.close()
	
		return mel_script_fn
		
	def createRIBGenScript(self):
		''' create the RIB gen script '''
		
		
		genrib_tms=''
		if self.preflight:
			genrib_tms='-rsm 0 -tms 0'
			
			
		args={'scenefile':self.scenefile,
		'wd':self.wd,
		'delight':self.delightversion,
		'maya':self.mayaversion,
		'maya_stub':maya_stub,
		'genrib_tms':genrib_tms,
		'camera':self.camera,
		'SHOW':self.envs['SHOW'],
		'SHOW_PATH':self.envs['SHOW_PATH'],
		'SCENE':self.envs['SCENE'],
		'SCENE_PATH':self.envs['SCENE_PATH'],
		'SHOT':self.envs['SHOT'],
		'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
		'sdl_path':self.paths['sdl_path'],
		'tdl_path':self.paths['tdl_path'],
		'shad_path':self.paths['shad_path'],
		'USER':self.user,
		'layer':self.layer,
		'resmult':self.resmult,
		'netcache_size':self.netcache_size,
		'render_pass':self.render_pass,
		'shader_collection':self.shader_collection_str,
		'render_cmd':self.render_cmd}	
				
		args['mel']=self.createAOVMelScript()
		
		
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

s=%s
e=%s

echo START :: $s
echo END :: $e

export SLICE="true"
echo SLICE :: $SLICE

export SLICE_PADDED=`printf "%%02d" $SGE_TASK_ID`

		''' % (self.start, self.start)
		
		
		#Generate BASH script
		maya_bash_script = open(self.paths['scripts_path']+"/maya_rib_gen.sh", 'w')
		
		maya_bash_script.write('''#!/bin/bash\n\

#
# RIB Generation script for : %(scenefile)s : Maya %(maya)s
#	

#$ -S /bin/bash
#$ -j y

unset SLICE
unset SLICE_PADDED

%(taskscript)s

export START=$s
export END=$e


#set workspace

source ${SOFTWARE}/bluebolt/envset/workspace %(WORKSPACE_PATH)s

export MAYA_APP_DIR=${TMPDIR}/maya;
export DELIGHT_VERSION=%(delight)s;
export MAYA_VERSION=%(maya)s;
export MAYA_MAJOR_VERSION=%(maya)s;
export MAYA_LOCATION=$SOFTWARE/maya/$UNAME.$DIST.$ARCH/%(maya)s;

unset DL_SHADERS_PATH
unset DL_DISPLAYS_PATH
unset DL_TEXTURES_PATH

mkdir -p %(sdl_path)s/$s
export _3DFM_OUTPUT_PATH=%(wd)s;
export _3DFM_SHADERS_PATH=%(sdl_path)s/$s;
export _3DFM_TEXTURES_PATH=%(tdl_path)s;
export _3DFM_SHADOWMAPS_PATH=%(shad_path)s;

echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo DELIGHT_VERSION::: $DELIGHT_VERSION
echo MAYA_VERSION::: $MAYA_VERSION
echo WORKSPACE_PATH=$WORKSPACE_PATH;

cmd="%(render_cmd)s -r 3delight -unc 1 -ncdir $TMPDIR/3delight/ -ncs %(netcache_size)d -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -resm %(resmult)d -verb -arwm 1 -lr %(layer)s -rp %(render_pass)s %(shader_collection)s -cam %(camera)s %(genrib_tms)s -rmode 1 -is false -an 1 -preRender 'source \"%(mel)s\";'  -s $s -e $e %(scenefile)s"
echo $cmd

function this_task(){

time %(render_cmd)s -r 3delight -unc 1 -ncdir $TMPDIR/3delight/ -ncs %(netcache_size)d -proj %(WORKSPACE_PATH)s/user/%(USER)s/maya/ -resm %(resmult)d -verb -arwm 1 -lr %(layer)s -rp %(render_pass)s %(shader_collection)s -cam %(camera)s %(genrib_tms)s -rmode 1 -is false -an 1 -preRender 'source "%(mel)s";'  -s $s -e $e %(scenefile)s

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task

''' % (args))

		maya_bash_script.close()
		
		return maya_bash_script

	def createRenderScript(self):
		
		if self.shader_collection not in ['<none>']:
			self.shader_collection_str='-sc %s' % self.shader_collection
		else:
			self.shader_collection_str="-sc \"\""
			
		
		if self.slices>1:
			self.step=1
		
		pre_ren_step=self.step
		
		if self.frames != '%d-%d' % (self.start,self.end) and self.frames == '0-0':
			self.frames='%d-%d' % (self.start,self.end)
		
		if self.slices>1:
			pre_ren_step=self.slices
			taskrange='1-%d' % (self.slices)
		
				
		rib_script_dep=''
		if self.preflight:
			rib_script_dep='preflight_script'
			self.scripts['preflight_script'] = {'script':self.createPreflightJobScript(),
											'type':2,
											'options':' -l dl=1 -tc %d ' % (self.max_slots),
											'name':'preflight',
											'frames':str(self.frames),
											'step':pre_ren_step}
			
		
		if self.bake:
			rib_script_dep='bake_script'
			self.scripts['bake_script'] = {'script':self.createBakeJobScript(),
										'type':2,
										'dep':'preflight_script',
										'options':' -l dl=1 -tc %d ' % (self.max_slots),
										'name':'bake',
										'frames':self.frames,
										'step':pre_ren_step}
			
		self.scripts['mel_script'] = {'script':self.createAOVMelScript(),'type':0}
		self.scripts['rib_script'] = {'script':self.createRIBGenScript(),
									'type':2,
									'options':' -l mem_free=4G -l dl=1 -tc %d ' % self.max_slots,
									'name':'ribgen',
									'frames':self.frames,
									'step':self.step}
		
		if rib_script_dep != '':
			self.scripts['rib_script']['dep']=rib_script_dep
		
		
		args={'scenefile':self.scenefile,
		'wd':self.wd,
		'delight':self.delightversion,
		'SHOW':self.envs['SHOW'],
		'SHOW_PATH':self.envs['SHOW_PATH'],
		'SCENE':self.envs['SCENE'],
		'SCENE_PATH':self.envs['SCENE_PATH'],
		'SHOT':self.envs['SHOT'],
		'WORKSPACE_PATH':self.envs['WORKSPACE_PATH'],
		'rib_file':'%s/%s_%s-%s' % (self.paths['rib_path'],self.prefix,'${s}','${e}'),
		'USER':self.user,
		'CPUS':self.cpus}	
		
		args['stats']=''
		
		if self.stats:
			args['stats']='-stats3'
		
		args['slicing_flags']=''
		
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
		
			args['slicing_flags']='-crop $crop_s $crop_e 0 1'
		
			args['rib_file']+='_${SLICE_PADDED}'
	
		render_script = open(self.paths['scripts_path']+"/render_script.sh", 'w')
		render_script.write('''#!/bin/bash
	
#
# Render script for : %(scenefile)s
#
#$ -S /bin/bash
#$ -j y
	
#simple calculator script
function calc {
	echo "scale=4; $1" | bc ;
}

#set workspace

source ${SOFTWARE}/bluebolt/envset/workspace %(WORKSPACE_PATH)s

#unset DL_SHADERS_PATH;

#export SHOW=%(SHOW)s;
#export SHOW_PATH=%(SHOW_PATH)s;
#export SCENE=%(SCENE)s;
#export SCENE_PATH=%(SCENE_PATH)s;
#export SHOT=%(SHOT)s;
#export WORKSPACE_PATH=%(WORKSPACE_PATH)s;

unset DL_SHADERS_PATH
unset DL_DISPLAYS_PATH
unset DL_TEXTURES_PATH

export DELIGHT_VERSION=%(delight)s;

%(taskscript)s

source /software/bluebolt/config/delight.env;
source /software/bluebolt/config/alembic.env;


# create the diskcache dir if not already there

if [ ! -d $TMPDIR/3delight ];then mkdir $TMPDIR/3delight; fi

echo umask :: `umask`
echo This Host ::: $HOSTNAME
echo User::: $USER
echo UNAME::: $UNAME
echo DIST::: $DIST
echo ARCH::: $ARCH
echo DELIGHT_VERSION::: $DELIGHT_VERSION
echo WORKSPACE_PATH=$WORKSPACE_PATH;

function this_task(){
cmd="time renderdl -frames $s $e %(slicing_flags)s -p $NSLOTS -progress %(stats)s %(rib_file)s.rib"

echo $cmd

echo Start :: `date`

if eval $cmd; then
  exitstatus=0
  rdl_es=$?
else
  rdl_es=$?
  exitstatus=100
fi

echo End :: `date`

echo ExitStatus :: $rdl_es

exit $exitstatus

}

eval this_task

''' % (args))
		
		render_script.close()
		
		self.scripts['render_script'] = {'script':render_script,
										'type':2,
										'dep':'rib_script',
										'options':' -l mem_free=4G -l dl=1 -tc %d' % (self.max_slots),
										'name':'delight',
										'frames':self.frames,
										'step':self.step}
		
		return render_script

	def createPostScripts(self):
		'''
			create the post job script, for running the clean up and post render processes
		'''
		
				
		if self.cleanup:

			args= {'scenefile':self.scenefile,
			'workingdir':self.wd,
			'outputdir':self.res_path}
			
			
	
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



		''' % (self.start, self.start)
		
			cleanup_script = open(self.paths['scripts_path']+"/cleanup.sh", 'w')
			cleanup_script.write('''#!/bin/bash
	
#
# Render script for : %(scenefile)s
#
#$ -S /bin/bash
#$ -j y

%(taskscript)s

function this_task(){

# delete ribs
find %(workingdir)s -name "*$s-$e.rib" -print0  | xargs -0 /bin/rm -fv

# delete shadowmaps
#find %(workingdir)s -name "*.dsm" -print0  | xargs -0 /bin/rm -fv
#find %(workingdir)s -name "*.shw" -print0  | xargs -0 /bin/rm -fv

eval "ls %(workingdir)s/shadows/*{$s..$e}.dsm | xargs /bin/rm -fv"
eval "ls %(workingdir)s/shadows/*{$s..$e}.shw | xargs /bin/rm -fv"


# clear ptcs and brickmaps
#find %(workingdir)s -name "*.ptc" -print0  | xargs -0 /bin/rm -fv
#find %(workingdir)s -name "*.bkm" -print0  | xargs -0 /bin/rm -fv

eval "ls %(workingdir)s/*/*/*/*{$s..$e}.ptc | xargs /bin/rm -fv"
eval "ls %(workingdir)s/*/*/*/*{$s..$e}.bkm | xargs /bin/rm -fv"

# clear shaders and sources
#find %(workingdir)s -name "*.sdl" -print0  | xargs -0 /bin/rm -fv
#find %(workingdir)s -name "*.sl" -print0  | xargs -0 /bin/rm -fv

ls %(workingdir)s/shaders/$s | xargs /bin/rm -Rfv

exitstatus=$?

if [ $exitstatus != 0 ];then
exit 100
fi

exit $exitstatus

}

eval this_task



''' % (args))
		
			cleanup_script.close()
			
		
			self.scripts['cleanup_script'] = {'script':cleanup_script,'type':2,'name':'cleanup','dep':'render_script'}
			
			
		if self.seqcheck:
			
			seqcheck_script = open(self.paths['scripts_path']+"/seqcheck.sh", 'w')
			
			seqcheck_script.write('''#!/bin/bash
#$ -S /bin/bash
#$ -j y
			
			export OPENEXR_VERSION=1.7.0;
			
			source $SOFTWARE/bluebolt/config/openexr.env;
			source $SOFTWARE/bluebolt/config/python.env;
			
			cd %(outputdir)s;
			
			$SOFTWARE/bluebolt/scripts/python/sequence_check.py -r -d %(workingdir)s/seqcheck ;
			''' % (args))
			
			seqcheck_script.close()
			
			self.scripts['seqcheck_script'] = {'script':seqcheck_script,'type':2,'name':'seqcheck','dep':'cleanup_script'}
			
		
			


	def _createQsubExecScript(self):
		''' 
			create the qsub submission script.
		'''
		
		
		exe="qsub -r y"
		
		if self.paused:
			exe+=" -h "
		
		
		if self.slices>1:
			self.step=1
			
			
		script = '''#!/bin/bash
	#
	# Submision Script for %s
	#			\n''' % (self.scenefile)
			
		for framerange in self.frames.split(','):
			
			
			args={'framerange':'%s-%s' % (framerange.split('-')[0],framerange.split('-')[-1]),
			'step':self.step,
			'email':'-m a -M %s@blue-bolt.com' % os.getenv('USER'),
			'jobname':self.name,
			'wd':self.wd,
			'max_slots':self.max_slots,
			'queue':self.queue,
			'rib_script':self.scripts['rib_script']['script'].name,
			'render_script':self.scripts['render_script']['script'].name,
			'logs_path':self.paths['log_path'],
			'exe':exe,
			'CPUS':self.cpus}
			
			args['taskrange']=args['framerange']
			args['rendertasks']=args['taskrange']
			args['pre_ren_step']=args['step']
			
			if self.slices>1:
				args['pre_ren_step']=self.slices
				args['taskrange']='1-%d' % (self.slices)
				args['rendertasks']='1-%d' % self.slices
				
				
				
			
			if self.preflight:
				args['preflight_script']=self.scripts['preflight_script']['script'].name
				
			if self.bake:
				args['bake_script']=self.scripts['bake_script']['script'].name
			
			
			if self.cleanup:
				args['cleanup_script']=self.scripts['cleanup_script']['script'].name
				
			# Make logs directory
			
			if not os.path.isdir(self.paths['log_path']):
				mkfolder(self.paths['log_path'])
				
			
			
			
			
			if not self.email:
				args['email']=''
			
			args['rib_wait'] = ''		
			
			if self.preflight:
				
				script+="%(exe)s -l mem_free=4G -l dl=1 -q %(queue)s  -t %(taskrange)s:%(pre_ren_step)d -tc %(max_slots)d %(email)s -N preflight.%(jobname)s -o %(logs_path)s -wd %(wd)s %(preflight_script)s;\n" % (args)
				args['rib_wait']='-hold_jid_ad preflight.%(jobname)s' % (args)
				
				
				
			if self.bake:
				args['bake_wait']=''
				if self.preflight:
					args['bake_wait']='-hold_jid_ad preflight.%(jobname)s' % (args)
					
				script+="%(exe)s -l mem_free=4G -l dl=1 -q %(queue)s -t %(taskrange)s:%(pre_ren_step)d -tc %(max_slots)d %(email)s %(bake_wait)s -N bake.%(jobname)s -o %(logs_path)s -wd %(wd)s %(bake_script)s;\n" % (args)
				args['rib_wait']='-hold_jid_ad bake.%(jobname)s' % (args)
				
			script+="%(exe)s -l mem_free=4G -l dl=1 -q %(queue)s -t %(rendertasks)s:%(step)d -tc %(max_slots)d %(email)s %(rib_wait)s -N ribgen.%(jobname)s -o %(logs_path)s -wd %(wd)s %(rib_script)s;\n" % (args)
			
			script+="%(exe)s -l mem_free=4G -pe render %(CPUS)s -l dl=1 -q %(queue)s  -t %(rendertasks)s:%(step)d -tc %(max_slots)d %(email)s -hold_jid_ad ribgen.%(jobname)s -N delight.%(jobname)s -o %(logs_path)s -wd %(wd)s %(render_script)s;\n" % (args)
			
			
			if self.cleanup:
				script+="%(exe)s -q %(queue)s -t %(rendertasks)s:%(step)d -tc %(max_slots)d -hold_jid_ad delight.%(jobname)s -N cleanup.%(jobname)s -o %(logs_path)s -wd %(wd)s %(cleanup_script)s;\n" % (args)
			
		f = open(self.paths['scripts_path']+"/"+args['jobname'], 'w')
		f.write(script)
		f.close()
	
		os.chmod(self.paths['scripts_path']+"/"+args['jobname'], 0775)
		
		# assign this script to the main script name
		
		self.script=f
		
		return f
		
	
	
	def makeScripts(self):		
		''' Generate the render scripts and the qsub submission script '''
		
		print 'generating scripts in ... %s' % self.wd
		
		if self.publishscene:
			
			mb_path = "%s/mb/" % (self.wd)
			
			if not os.path.isdir(mb_path):
				mkfolder(mb_path)		
			
			publishedfile="%s/%s" % (mb_path,os.path.basename(self.scenefile))
			
			if not os.path.isfile(publishedfile):
				print "Copying scene file ..."
				org_size=os.path.getsize(self.scenefile)
				shutil.copyfile(self.scenefile,publishedfile)
			
			
			self.scenefile = publishedfile
		
		
		
		self.createRenderScript()
		self.createPostScripts()
		#self.createQsubExecScript()
	
		return self.createQsubExecScript()
		
	
	def output(self):
		''' Return a string of stats about this job submission '''		
		
		self.extra_data={
			'scenefile':self.scenefile,
			'slices':self.slices,		
			'aovs':','.join(self.aovs),		
			'layer':self.layer,		
			'render_pass':self.render_pass,	
			'maya_version':self.mayaversion,
			'3delight_version':self.delightversion,	
			'preflight':self.preflight,	
			'cleanup':self.cleanup,	
			'resolution':','.join(self.res.values()),
			'version':self.version,	
			'frames':self.frames,
			'outputdir':os.path.dirname(self.paths['img_path'])
		}
		
		
		this_resmult=['full','half','quater','eigth']
		
		output = "submitting job...: %s \n" % self.name
		output+= "working dir......: %s \n" % self.wd
		output+= "output dir.......: %s \n" % self.res_path
		output+= "scenefile........: %s \n" % self.scenefile
		output+= "version..........: %d \n" % self.version
		output+= "frames...........: %s \n" % self.frames
		output+= "resolution.......: %dx%d \n" % (int(self.res['width']),int(self.res['height']))
		output+= "step.............: %d \n" % int(self.step)
		output+= "slices...........: %d \n" % int(self.slices)
		output+= "stats............: %s \n" % self.stats
		output+= "aovs.............: %s \n" % ','.join(self.aovs)
		output+= "camera...........: %s \n" % self.camera
		output+= "layer............: %s \n" % self.layer
		output+= "queue............: %s \n" % self.queue
		output+= "cpus.............: %s \n" % self.cpus
		output+= "max slots........: %d \n" % int(self.max_slots)
		output+= "res multiplier...: %s \n" % this_resmult[int(self.resmult)]
		output+= "renderpass.......: %s \n" % self.render_pass
		output+= "shader collection: %s \n" % self.shader_collection
		output+= "maya version.....: %s \n" % self.mayaversion
		output+= "3delight.........: %s \n" % self.delightversion
		output+= "preflight........: %s \n" % str(self.preflight)
		output+= "cleanup..........: %s \n" % str(self.cleanup)
		output+= "send disabled....: %s \n" % str(self.paused)
				
		return output
		
	