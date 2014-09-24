
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
#    Version:1.0.1

"""
    Main Arnold class

    Has two main jobs:
     
     assgen -- generate the ass files from maya (if neccecery)
     
     kick -- do the render
    
    Postprocess :

     cleanup -- clear the ass files after successfull render

     sequence-check

     contact-sheet
"""

from gridengine import Job,JobType,mkfolder,Queue
from gridengine.Exceptions import *

# lets import the types of job this one relies upon
import MayaBatch
import Command

import os as _os 

# TODO: Kick job based AOVS


class KickJob(Command.CommandJob):
    ''' Job that does the Arnold standalone render with the kick application '''
    def __init__(self,jid=None):
        super(KickJob, self).__init__(jid)
        
        # Grid options
        self.label = "kick_job"
        self.type = JobType.ARRAY
        self.queue = Queue("3d.q")
        self.scenefile = "test.ass"
        self.args = " -dp -dw"
        self.userArgs = ""
        # self.options = " -l arnold=1"    
        self.resources = {'hard':[('arnold',1)],'soft':[('arnold_inuse',True)]}     
        self.camera = None
        self.frames = "1-10"
        self.step = 1
        self.publish_scene = False
        
        self.arnold_version = "4.0.15.1"
        self.arnold_plugin_path = ""
        self.render_cmd = "${SOFTWARE}/wrappers/kick"

        # Kick options, any value set to -1 will use the scene settings instead
        self.image_scale = 1.0
        self.verbosity = 2 # 1..6, 2 = progress messages
        self.res = {'width':-1,'height':-1}  # resolution
        self.ar = -1 # pixel aspect ratio
        self.overscan = -1 # overscan in pixels (int) or percentage (%float)
        self.aas = -1 # anti-aliasing samples default:4 draft:2 production:8
        self.bs = -1 # set the bucket size
        self.subd = -1 # set the max subdivision surface level

        # Advanced Options
        self.force_expand = False
                
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
        
        # Set the default versions based upon current environment
        
        if _os.environ.has_key('ARNOLD_VERSION'):
            self.arnold_version = _os.environ['ARNOLD_VERSION']
        if _os.environ.has_key('ARNOLD_PLUGIN_PATH'):
            self.arnold_plugin_path = _os.environ['ARNOLD_PLUGIN_PATH']

        
            
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
        
        # set the custom args for the renderer
        
        self.args += " -t $NSLOTS" # number of threads set to the gridengine ENV $NSLOTS, the number of slots given to the job, this makes it so we can change the number of threads live on the job

        self.args += " -v %d" % self.verbosity # set the verbosity

        # Now for the overrides

        if self.camera:
            self.args += " -c %s" % self.camera # set the custom args for the renderer
        
        if self.image_scale != 1.0:
            self.args += " -sr %f" % self.image_scale # set the image scale multiplier (defailt 1.0)
                
        if self.bs != -1:
            self.args += " -bs %d" % self.bs # set the bucket size
        
        if self.aas != -1:
            self.args += " -as %d" % self.aas # set the anti-aliasing samples
        
        if self.subd != -1:
            self.args += " -sd %d" % self.subd # set the max subdivisions
        
        if self.res['width'] != -1 and self.res['height'] != -1:
            self.args += " -r %(width)d %(height)d" % self.res # set the resolution
                        
        if self.ar != -1:
            self.args += " -ar %f" % self.ar # set the resolution

        if self.overscan != -1:
            pass
                        
        if self.force_expand:
            self.args += " -forceexpand" # force expand procedurals

        if self.disable_atmosphere:
            self.args += " -ia" # Ignore atmosphere shaders
            
        if self.disable_background:
            self.args += " -ib" # Ignore background shaders
        
        if self.disable_bump:
            self.args += " -ibump" #  Ignore bump-mapping
            
        if self.disable_direct_lighting:
            self.args += " -idirect" # Ignore direct lighting
        
        if self.disable_displacement:
            self.args += " -idisp" # Ignore displacement
        
        if self.disable_lights:
            self.args += " -il" # Ignore lights
        
        if self.disable_motion_blur:
            self.args += " -imb" # Ignore motion blur
            
        if self.disable_shaders:
            self.args += " -is" # Ignore shaders
        
        if self.disable_shadows:
            self.args += " -id" # Ignore shadows
        
        if self.disable_sss:
            self.args += " -isss" # Ignore sub-surface scattering
        
        if self.disable_subds:
            self.args += " -sd" # Ignore mesh subdivision
        
        if self.disable_textures:
            self.args += " -it"  # Ignore texture maps

        if self.userArgs != "": # any other user arguments
            aels.args += " %s " % self.userArgs
        
        # do any additional envs that might be needed
        
        self.envs['ARNOLD_VERSION'] = self.arnold_version
        if self.arnold_plugin_path:
            self.envs['ARNOLD_PLUGIN_PATH'] = self.arnold_plugin_path
        
        for _app in ['ilmbase','openexr','alembic','cortex']:
            _key = _app.upper()+'_VERSION'
            if _os.environ.has_key(_key):
                self.envs[_key] = _os.environ[_key]

        # catch if this job has depeneded on a ass gen job
        
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
#            this_sn += '.$f.'
#            this_sn += '.'.join(split_scenename[-2:])
            
            self.scenefile = _os.path.join(scene_file_dirname,this_sn)
            
        self.cmd = '%s %s -i %s' % (self.render_cmd,self.args,self.scenefile)
        
        # Now run the command job setups ...
        super(KickJob,self).createJobScript()
        
        return self.script
    
    
    def output(self):
        ''' generate job infomation output '''
        
        
        output = "submitting job...: %s \n" % ('.'.join([self.label,self.name]))
        output+= "command..........: %s \n" % self.cmd
        output+= "working dir......: %s \n" % self.wd
        output+= "send disabled....: %s \n" % str(self.paused)
        output+= "camera...........: %s \n" % str(self.camera)
        if len(self.dependency_list):
            name_list = []
            for dep in self.dependency_list:
                name_list.append('.'.join([dep.label,dep.name]))
            output+= "depends on.......: %s \n" % ','.join( name_list )
                
        return output
    

class MayaAssGenJob(MayaBatch.MayaBatchJob):
    ''' Sub-Class instancve of the maya render job that generates ass files from a maya scene file '''

    def __init__(self,jid=None):
        super(MayaAssGenJob,self).__init__(jid)
        
        self.label = "maya_ass_gen"
        self.type = JobType.ARRAY
        self.queue = Queue("3d.q")    
        self.arnold_version = _os.environ['ARNOLD_VERSION'] if _os.environ.has_key('ARNOLD_VERSION') else "4.0.5.3"
        self.mtoa_version = _os.environ['MTOA_VERSION'] if _os.environ.has_key('MTOA_VERSION') else "0.19.0.dev"
        self.maya_version = _os.environ['MAYA_VERSION'] if _os.environ.has_key('MAYA_VERSION') else "2012"
        self.arnold_plugin_path = ""
        if _os.environ.has_key('ARNOLD_PLUGIN_PATH'):
            self.arnold_plugin_path = _os.environ['ARNOLD_PLUGIN_PATH']
        self.scenefile = 'arnold_maya_scene.mb'
        self.aovs ={} # aovs dict : aovs['beauty']={'data':'rgba','driver':{'name':'exr.1','translator':'exr','options':{'exrCompression':'zips','halfPrecision':True,'tiled':False,'autocrop':True,'mergeAOVs':True}},'filter':('blackman_harris',4.0)}
        self.addbeauty = True # add a beauty (RGBA) aov if it does not already exist
        self.publish = True
        self.renderlayer = 'defaultRenderLayer'
        self.camera = None
        self.ass_file = '' # output ass_file name
        self.padding = 4 # Frame padding
        self.render_pass=''

        # output options

        self.image_prefix = "%s_<RenderLayer>_lnh_v%03d" % (self.envs['WORKSPACE'],self.version)
    
    def createPythonScript(self,export_file_path):
        """ Generate a python script for setting the AOVS and ouput of the render """
        
        
        if not _os.path.isdir(self.paths['scripts_path']):
            mkfolder(self.paths['scripts_path'])
        
        #Generate preflight BASH script
        python_script = open(self.paths['scripts_path'] + "/aovs.py", 'w')

        _beautydata = { 'data':'rgba',
                        'driver':{'name':'exr1',
                                  'translator':'exr',
                                  'options':{'exrCompression':'zips',
                                             'halfPrecision':True,
                                             'tiled':False,
                                             'autocrop':True,
                                             'mergeAOVs':True
                                             }
                                },
                        'filter':('blackman_harris',4.0)
                        }
                
        if self.aovs == {} : # If there are no AOVS given then auto add the beauty aov RGBA
            self.aovs = {'RGBA':_beautydata}

        # add the RGBA aov if it is required, checking if either RGBA or beauty is allready in aovs list
        if not any(el in set(self.aovs.keys()) for el in ['RGBA','beauty']) and self.addbeauty:
            self.aovs['RGBA'] = {'data':'rgba'}
        
        py_str="""
aovs = {}
"""
        for aov in self.aovs:
            py_str+="aovs['%s']=%s\n"%(aov,str(self.aovs[aov]))

        py_str+="""
print "="*35
print "Setting AOVS";

import os
import pymel.core as pm
import mtoa
"""
        if -1 in self.res.values(): # 
            py_str += """

###################################

# Change the output folder so that it is the resolusion of the scene,
# this happens when no resolution was given to the submitter

res_node = pm.PyNode('defaultResolution')
width=res_node.width.get()
height=res_node.height.get()

i = iter(workspace(q=True,fr=True))

current_loc = os.path.abspath(dict(zip(i, i))['images'])
dirname = os.path.dirname(current_loc) 
new_loc = os.path.join(dirname,'x'.join([str(width),str(height)]))

print "Setting output to %s" % new_loc

pm.mel.eval('workspace -fileRule "depth" "%s"' % new_loc )
pm.mel.eval('workspace -fileRule "images" "%s"' % new_loc )  # set the output directory


####################################
"""
        py_str+="""

# General Maya stuff

drg = pm.PyNode('defaultRenderGlobals')

drg.imageFilePrefix.set('%(image_prefix)s')

""" % self.__dict__

        py_str +="""

# MTOA Stuff
render_options = mtoa.aovs.AOVInterface()

# Disable the default driver

dd=pm.PyNode('defaultArnoldDriver')
dd.outputMode.set(0)

dflt_drv = pm.createNode('aiAOVDriver',name='default_exr_driver')
dflt_drv.aiTranslator.set('exr')
dflt_drv.exrCompression.set('zips')
dflt_drv.halfPrecision.set(True)
dflt_drv.autocrop.set(True)
dflt_drv.tiled.set(False)
dflt_drv.mergeAOVs.set(True)

# keep the scene aovs if we havn't been given any
if not len(aovs):
    for scene_aov in ls(type='aiAOV'):
        dflt_drv.message >> scene_aov.attr('outputs[0].driver')
else:
    render_options.removeAOVs(mtoa.aovs.getAOVs())

driver_dict={}
for aov in aovs:
    print "Adding AOV : %s" % aov
    # Make our grid driver for this aov
    ad = dflt_drv
    if aovs[aov].has_key('driver'):
        drv_name = 'Grid_driver_%s' % (aovs[aov]['driver']['name'])
        drv_type = aovs[aov]['driver']['translator']
        if drv_type not in ['ie','exr'] : # if it is set the the ie display driver just use the default exr one, or if this is tan exr one use the default also
            if drv_name not in driver_dict.keys():
                ad=pm.createNode('aiAOVDriver',name=drv_name)
                ad.aiTranslator.set(aovs[aov]['driver']['translator'])
                for opt in aovs[aov]['driver']['options']:
                    if ad.hasAttr(opt):
                        print ad,opt,aovs[aov]['driver']['options'][opt]
                        ad.setAttr(opt,aovs[aov]['driver']['options'][opt])
                ad.outputMode.set(1)
                driver_dict[drv_name]=ad
            else:
                ad = driver_dict[drv_name]

    # Filter

    af = None    
    if aovs[aov].has_key('filter'):
        flt_name = 'Grid_%s_%s_filter' % (aov,aovs[aov]['filter'][0])
        af=pm.createNode('aiAOVFilter',name=flt_name)
        af.aiTranslator.set(aovs[aov]['filter'][0])
        if len(aovs[aov]['filter']) > 1:
            af.width.set(aovs[aov]['filter'][1])        
    
    aov_object = render_options.addAOV(aov)
    if aovs[aov].has_key('data') and aovs[aov]['data']:
        aov_object.node.attr('type').set(aovs[aov]['data'])

    ad.message >> aov_object.node.attr('outputs[0].driver')
    if af:
        af.message >> aov_object.node.attr('outputs[0].filter')

print "="*35

settings={'START':os.environ['START'],'END':os.environ['END']}

try:
""" 
        cam_str = ''
        if self.camera != None:
            cam_str =" -cam \"%s\"" % self.camera
        if self.render_pass and self.render_pass != 'None':
            fullRenderPass='-ps %s'%self.render_pass
        else:
            fullRenderPass=''
        settings_dict={'out_ass':export_file_path,'camera':cam_str, 'render_pass':fullRenderPass}

        # py_str+="   pm.currentTime(int(settings['START']))\n" # set frame to the start of the sequence
        py_str+="   pm.setAttr('time1.outTime', int(settings['START']))\n" # set frame to the start of the sequence


        py_str+="   mel_cmd = 'arnoldExportAss -b  %(render_pass)s -f \"%(out_ass)s\" -lightLinks 1 -shadowLinks 1 %(camera)s -sf %%(START)s -ef %%(END)s -fs 1'%%settings\n"%settings_dict
        py_str+="   print 'mel_cmd :: %s'%mel_cmd\n"
        py_str+="   res = pm.mel.eval(mel_cmd)\n"
        py_str+="   if res == None:\n"
        py_str+="       raise Exception('Failed to create ass file')\n"

        py_str+="""except:
    pm.mel.eval('quit -abort -f -exitCode 100')
    print "Error: there was an error when executing 'arnoldExportAss' command"
else:
    pm.mel.eval('quit -abort -f -exitCode 0')
"""

        python_script.write(py_str)
        
        python_script.close()
        
        return python_script.name
        
    
    def createJobScript(self):
        """ Main job bash script generator """
        
        self.args = "" # set the custom args for the renderer
        
        self.envs['MTOA_VERSION'] = self.mtoa_version
        self.envs['ARNOLD_VERSION'] = self.arnold_version
        self.envs['ARNOLD_PLUGIN_PATH'] = self.arnold_plugin_path
        
        self.paths['ass_path'] = '%s/ass' % self.wd
        
        slash_quote = '\\'*3
        
        # Set the image name we do this in each ass_gen job so the naming is in keeping with the choosen 3rd part method
        img_name = "%s_\<RenderLayer\>_lnh_v%03d" % (self.envs['WORKSPACE'],self.version)
        
        s_file = _os.path.splitext(self.scenefile)
        
        assfile = '%s_<RenderLayer>.ass' % (_os.path.basename(s_file[0]))
        export_file_path = _os.path.join(self.paths['ass_path'],assfile)  
        # the export command for mtoa
        
        export_cmd = 'arnoldExportAss -b '
        export_cmd += '-f %s"%s%s" ' % (slash_quote,export_file_path,slash_quote)
        export_cmd += '-asciiAss -mask 255 -lightLinks 1 -shadowLinks 1 '
        export_cmd += '-cam %s"%s%s" ' % (slash_quote,self.camera,slash_quote)
        export_cmd += '-c -sf $START -ef $END -fs 1 '
        
        aovs_py=self.createPythonScript(export_file_path)

        bat_settings = {'sq':slash_quote,'rl':self.renderlayer,'xc':export_cmd,'ip':self.paths['img_path'], 
                        'pad':self.padding,'in':img_name}
        
        # now for the mel command to send to to maya batch
        
        batch_cmd = ['editRenderLayerGlobals -crl %(rl)s' % bat_settings ]# set render layer        
        batch_cmd.append('disableImagePlanes') # Disable any image planes in the scene
        batch_cmd.append('workspace -fileRule %(sq)s"depth%(sq)s" %(sq)s"%(ip)s%(sq)s"' % bat_settings )
        batch_cmd.append('workspace -fileRule %(sq)s"images%(sq)s" %(sq)s"%(ip)s%(sq)s"' % bat_settings ) # set the output directory
        batch_cmd.append('setAttr defaultRenderGlobals.extensionPadding %(pad)d' % bat_settings ) # set Padding             
        # batch_cmd.append('setAttr -type %(sq)s"string%(sq)s" defaultRenderGlobals.imageFilePrefix %(sq)s"%(in)s%(sq)s"' % bat_settings ) # set image name
        batch_cmd.append('setMayaSoftwareFrameExt\(%(sq)s"3%(sq)s", 1\)' % bat_settings ) # set image padding format to name.#.ext     
        
        # Generate the aovs.mel for this render

        if _os.path.isfile(aovs_py):
            bat_settings['aovs_py'] = aovs_py       
            batch_cmd.append( 'python\(%(sq)s"execfile\(\\\'%(aovs_py)s\\\'\)%(sq)s"\)' % bat_settings )
               
        #batch_cmd += "if \( catch\( %(sq)s`%(xc)s%(sq)s` \) \) quit -a -f -exitCode 100\;quit -a -f -exitCode 0\;" % bat_settings
        
        # bring it all together
        self.args = "-command '%s'" % '\;'.join(batch_cmd)
        
        # check and set the output file name

        if self.renderlayer == 'defaultRenderLayer':self.renderlayer='masterLayer'
        firstframe = '%s_%s.%04d.ass' % (_os.path.basename(s_file[0]),self.renderlayer,int(self.frames.split('-')[0]))
        
        self.ass_file = _os.path.join(self.paths['ass_path'],firstframe)        
        
        # run the inherited creatJobScript method with our additional arguments
        super(MayaAssGenJob,self).createJobScript() 
                
        return self.script
        
    
class HoudiniAssGenJob(Job):
    ''' Houdin based generator for creating .ass files for Arnold from HtoA'''
        
    def __init__(self,jid=None):
        super(HoudiniAssGenJob,self).__init__(jid)
        
        
    
class ArnoldJob(Job):
    ''' Main Arnold job class this is the parent of any ass generator or kick render job'''
    
    def __init__(self,jid=None):
        super(ArnoldJob, self).__init__(jid)
        self.label = 'arnold'
        self.queue = Queue('3d.q')
        
        self.cleanup = True
        self.seqcheck = False        
        self.publish = True
        self.ass_file=''
        self.scenefile = '' #: can be maya ma/mb or arnold ass file
        self.mayafile = '' #: can only be a mayascene file (.ma/.mb)
        self.arnold_version = _os.environ['ARNOLD_VERSION'] if _os.environ.has_key('ARNOLD_VERSION') else "4.0.12.0"
        self.mtoa_version = _os.environ['MTOA_VERSION'] if _os.environ.has_key('MTOA_VERSION') else "0.22.0"
        self.maya_version = _os.environ['MAYA_VERSION'] if _os.environ.has_key('MAYA_VERSION') else "2012"

        self.envs.update({'ARNOLD_VERSION':_os.environ['ARNOLD_VERSION'] if _os.environ.has_key('ARNOLD_VERSION') else "4.1.3.3",
                          'MTOA_VERSION':_os.environ['MTOA_VERSION'] if _os.environ.has_key('MTOA_VERSION') else "1.0.0.1",
                          'MAYA_VERSION':_os.environ['MAYA_VERSION'] if _os.environ.has_key('MAYA_VERSION') else "2014",
                          'ALEMBIC_VERSION':_os.environ['ALEMBIC_VERSION'] if _os.environ.has_key('ALEMBIC_VERSION') else "1.5.0.1"
}            )
        
        self.version = None # use to override the version that is sent/rendered.
        self.slices = 0
        self.assGen_Cpus = 1 # set the number of CPUs to use in creating ass files.
        
        self.prefix = 'test_render'
        self.outFrames = ""
        self.use_showAOVS = False
        
        # Maya Scene options
        self.layer = 'defaultRenderLayer'
        self.render_pass = None
        self.camera = None
        self.addbeauty = True # add a beauty (RGBA) aov if it does not already exist        
        self.aovs = {} # aovs dict : aovs['beauty']={'data':'rgba','driver':{'name':'exr.1','translator':'exr','options':{'exrCompression':'zips','halfPrecision':True,'tiled':False,'autocrop':True,'mergeAOVs':True}},'filter':('blackman_harris',4.0)}

        self.image_prefix = 'test_<RenderLayer>' #: set the base name for the output image

        # Kick options
        self.image_scale = 1.0
        self.verbosity = 2
        self.res = {'width':-1,'height':-1}   
        self.ar = -1 # aspect ratio 
        self.aas = -1 # anti-aliasing samples default:-1 draft:2 production:8
        self.bs = -1 # arnold bucket sizes
        self.subd = -1 # set the max subdivision surface level

        self.overscan = -1 # the overscan for this render, in pixels or percentage
        
        self.force_expand = False
        self.userArgs = "" # user arguments for kick
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
        
    
    def setJobName(self):
        ''' Generate a time stamped name for this Job '''
        dt=self.dt.strftime('%Y%m%d%H%M%S')
        self.prefix=_os.path.basename(_os.path.splitext(self.scenefile)[0])+"_"+self.layer+"_"+str(self.render_pass)
        self.name=self.prefix+'.'+str(dt)
    
    
    def setVersion(self):
        ''' check and set the version based on the render_tmp location '''
        
        if self.paths.has_key('out_dir'):
            
            if not self.version: # if the version has not been set detect it
                self.version = 1
                        
                if _os.path.isdir(self.paths['out_dir']):
                    dirlist=_os.listdir(self.paths['out_dir'])
                    dirlist.sort()
                    for d in  dirlist:
                        if d.startswith("v"):
                            self.version = int(d.strip('v'))+1    # legacy published version folders 
    
            
    def setPaths(self):
        ''' Set the paths for pantry based resources '''
        
        #
        # Changed for the renders to go to the user directory
        #

        if not 'out_dir' in self.paths : self.paths['out_dir']="%s/renders/%s/%s/" % (self.envs['USER_PATH'],self.layer,str(self.render_pass))
                
        self.setVersion() # everything below relys on the version being set

        self.paths['pantry'] = _os.path.join(self.paths['out_dir'],"v%03d"%self.version,'.pantry')

        self.setWD(self.paths['pantry'])

        mkfolder(self.wd)
        
        self.paths['ass_path'] = '%s/ass' % self.wd
        
        self.paths['mb_path'] = '%s/mb' % self.wd
        
        self.paths['scripts_path'] = '%s/scripts' % self.wd
        
        if not 'img_path' in self.paths : self.paths['img_path'] = "%s/v%03d/%s" % (str(self.paths['out_dir']),int(self.version),'x'.join( map(str, self.res.values()) ) )

        if 'WORKSPACE' in self.envs:
            self.image_prefix = "%s_<RenderLayer>_lnh_v%03d" % (self.envs['WORKSPACE'],self.version)
        else:
            self.image_prefix = "%s_<RenderLayer>_lnh_v%03d" % (self.envs['WORKSPACE'],self.version)

    def setOutDir(self,out_dir):
        """
        Set the output directory for the renders , this will reset the version to None and autoset up the child folders
        """

        self.paths['out_dir']=out_dir
        self.version=None
        self.setPaths()

    def setOutImagePath(self,out_image_path):

        self.paths['img_path'] = out_image_path

        
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
        ass_job.cpus = self.assGen_Cpus    
        ass_job.aovs = self.aovs
        ass_job.addbeauty = self.addbeauty 
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
        ass_job.image_prefix = self.image_prefix
        ass_job.render_pass=self.render_pass
        
        if self.ass_file:
            ass_job.ass_file=self.ass_file       
                                  
        return ass_job 
    
    def createKickJob(self):
        ''' Make main kick job instance '''
        
        kick_job = KickJob()
        
        # Grid stuff
        kick_job.name = self.name    
        kick_job.wd = self.wd        
        kick_job.paths = self.paths
        kick_job.envs = self.envs
        kick_job.envs['MAYA_VERSION'] = self.maya_version
        kick_job.envs['MTOA_VERSION'] = self.mtoa_version

        kick_job.queue = self.queue    
        kick_job.paused = self.paused
        kick_job.cpus = self.cpus
        kick_job.max_slots = self.max_slots
        
        kick_job.camera = self.camera
        kick_job.publish = self.publish
                
        
        kick_job.res = self.res
        kick_job.ar = self.ar

        kick_job.overscan = self.overscan
        kick_job.image_scale = self.image_scale
        kick_job.verbosity = self.verbosity
        
        kick_job.aas = self.aas
        kick_job.bs = self.bs
        kick_job.subd = self.subd
        
        kick_job.force_expand = self.force_expand

        kick_job.userArgs = self.userArgs

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
        kick_job.render_pass=self.render_pass        
        kick_job.frames = self.frames
        #kick_job.args = self.args # add any custom arguments to the kick commandline
        
        if self.ass_file:
            kick_job.ass_file =self.ass_file 
        kick_job.scenefile = self.scenefile # arnold autodetects frames in the file name so this can be a file with out or with the frame number in its name.
        
        kick_job.parent = self        
        
        
        return kick_job    

    def createCleanUpJob(self):
        ''' Make the Clean up job that relies up on the the end of the main kick render  '''

        cleanup_job = Command.CommandJob()
        cleanup_job.name = self.name     
        cleanup_job.label = 'clean_up'
        cleanup_job.type = JobType.ARRAY
        cleanup_job.queue = Queue("3d.q")
        cleanup_job.parent = self 
        cleanup_job.wd = self.wd        
        cleanup_job.paths = self.paths
        cleanup_job.envs = self.envs
        cleanup_job.queue = self.queue    
        cleanup_job.paused = self.paused
        cleanup_job.cpus = 1
        cleanup_job.max_slots = self.max_slots

        cleanup_job.frames = self.frames

        cleanup_job.prescript = 's=$SGE_TASK_ID\n'
        cleanup_job.prescript += 'e=`echo $[$s+$SGE_TASK_STEPSIZE-1]`\n'
        cleanup_job.prescript += 'if [ $e -ge $SGE_TASK_LAST ]; then\n'
        cleanup_job.prescript += 'e=$SGE_TASK_LAST;\n'
        cleanup_job.prescript += 'fi\n'

        if len(self.frames.split('-')) > 1:
            # Set the step to 1 as Mtoa would have spit out a file per frame
            cleanup_job.step = 1      
            # change pre script as such to add a padded number for this frame
            cleanup_job.prescript += '''
f=`printf "%04d" $SGE_TASK_ID`
'''
            cleanup_job.cmd = 'find %s -name \\"*.$f.ass.*\\" -print0  | xargs -0 /bin/rm -fv' % self.wd
        else:
            cleanup_job.cmd = 'find %s -name \\"*.ass*\\" -print0  | xargs -0 /bin/rm -fv' % self.wd

        
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
        
        if _os.path.splitext(r_file.lower())[-1] in ('.mb','.ma'): # is the input scenefile a maya file? If so make a MayaAssGenjob
            ass_job = self.createMayaAssGenJob()
            self.children.append( ass_job )
            ass_job.createJobScript() # run the job script generator this should fill in any extra details needed later
                        
            self.paths['img_path'] = ass_job.paths['img_path']
            self.mayafile = ass_job.scenefile
            self.scenefile = ass_job.ass_file

            g = globals()
            for n in g:
                if g[n] == None: print n,g[n]
            
        # Now make the Kick Job, if necceceary set the dependence on the above AssGenJob
        
        if '.ass' in self.scenefile.lower():

            kick_job = self.createKickJob()
            
            if ass_job:
                kick_job.dependency_list = [ass_job]
                kick_job.publish_scene = False # we don't want to publish any ass files from this automatic job
            
            kick_job.createJobScript()
            
            self.children.append(kick_job)  
            
            # Add now the Clean-Up Job which depends on the kick job        
            
            if self.cleanup:
                cleanup_job = self.createCleanUpJob()
                
                cleanup_job.dependency_list = [kick_job]
                
                cleanup_job.createJobScript()
            
                self.children.append(cleanup_job) 
        else:
            raise NoFileError(self.scenefile)


        # reset back the scenefile to the original if it was a maya file before

        if self.mayafile:
            self.scenefile = self.mayafile

        # if the main arnold job has been given a dependency feed it to the first child of this job        
        if self.dependency_list != []:
            self.children[0].dependency_list = self.dependency_list
                
        return self.children
    
    def output(self):
        ''' generate job infomation output '''
        
        env_list = list()
        for k in self.envs: env_list.append( "%s=%s" % (k,self.envs[k]) )
                
        self.extra_data={
                        'scenefile':self.scenefile,
                        'maya_version':self.maya_version,
                        'arnold_version':self.arnold_version,
                        'frames':self.frames,
                        'env': ';'.join(env_list),
                        'layer':self.layer,
                        'pass':str(self.render_pass)                
                        }
        
        if hasattr(self, 'mayafile'):
            self.extra_data['mayafile'] = self.mayafile
        
        output = "submitting job...: %s \n" % self.name
        output+= "command..........: %s \n" % self.cmd
        output+= "working dir......: %s \n" % self.wd
        output+= "send disabled....: %s \n" % str(self.paused)
                
        return output
