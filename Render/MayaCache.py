
'''

    Generic maya render job class, used by other renderers for running pre-flight and generic render commands.

'''

from gridengine import Job,JobType,mkfolder,Queue
from gridengine.Exceptions import *
from gridengine.Utils import copyFile

import MayaBatch

import os as _os


class MayaCacheJob(MayaBatch.MayaBatchJob):
    ''' Sub-Class instancve of the maya render job that generates ass files from a maya scene file '''

    def __init__(self,jid=None):
        super(MayaCacheJob,self).__init__(jid)
        
        self.label = "maya_cache"
        self.type = JobType.SINGLE
        self.queue = Queue("3d.q")    
        self.maya_version = _os.environ['MAYA_VERSION'] if _os.environ.has_key('MAYA_VERSION') else "2014"
        self.scenefile = 'maya_scene.mb'
        self.publish = True # make a copy of the simulation input maya file
        self.renderlayer = 'defaultRenderLayer' # the render layer to use

        # output options
        self.outputdir = '/non/existent/path'
        self.cachename = 'myCacheName'
        self.cacheableNode = None # the name of the node you want to cache
        self.cachedistribution = 'OneFilePerFrame' # can be 'OneFilePerFrame' or 'OneFile'

    
    def createPythonScript(self):
        """ Generate a python script for setting the AOVS and ouput of the render """
        
        
        if not _os.path.isdir(self.paths['scripts_path']):
            mkfolder(self.paths['scripts_path'])
        
        #Generate preflight BASH script
        python_script = open(self.paths['scripts_path'] + "/doCache.%s.py"%( self.dt.strftime('%Y%m%d%H%M%S') ), 'w')

        for fr in self.frames.split(','):
            args = {
            'cachedistribution':self.cachedistribution,
            'start':int(fr.split('-')[0]),
            'end':int(fr.split('-')[-1]),
            'cachename':self.cachename,
            'cacheableNode':self.cacheableNode,
            'outputdir':self.outputdir
            }
                    
            py_str="""
import os
import pymel.core as pm

pm.cacheFile(cacheFormat="mcx",format="%(cachedistribution)s",st=%(start)d,et=%(end)d,directory="%(outputdir)s",f="%(cachename)s",cacheableNode="%(cacheableNode)s")
""" % args

            python_script.write(py_str)
        
        python_script.close()
        
        return python_script.name
        
    
    def createJobScript(self):
        """ Main job bash script generator """
        
        self.args = "" # set the custom args for the renderer
        
        self.envs['MAYA_VERSION']=self.maya_version

        slash_quote = '\\'*3
        
        s_file = _os.path.splitext(self.scenefile)
        # the export command for mtoa
                
        cache_py=self.createPythonScript()

        bat_settings = {'sq':slash_quote,'rl':self.renderlayer,'cache_py':cache_py}
        
        # now for the mel command to send to to maya batch
        
        batch_cmd = ['editRenderLayerGlobals -crl %(rl)s' % bat_settings ]# set render layer 
        batch_cmd= ['python\(%(sq)s"execfile\(\\\'%(cache_py)s\\\'\)%(sq)s"\)' % bat_settings ]
            
        # bring it all together
        self.args = "-command '%s'" % '\;'.join(batch_cmd)
        
        # check and set the output file name

        if self.renderlayer == 'defaultRenderLayer':self.renderlayer='masterLayer'
        
        # run the inherited creatJobScript method with our additional arguments
        super(MayaCacheJob,self).createJobScript() 
                
        return self.script


    def output(self):
        ''' Submit this job to gridengine '''
        
        self.extra_data={
            'maya_scene':self.scenefile,
            'maya_version':self.maya_version
        }
        
        
        output = "submitting job...: %s \n" % self.name
        output+= "working dir......: %s \n" % self.wd
        output+= "Maya File........: %s \n" % self.scenefile
        output+= "Maya Version.....: %s \n" % self.maya_version
        output+= "cpus.............: %d \n" % int(self.cpus)
        output+= "queue............: %s \n" % self.queue.name
        output+= "send disabled....: %s \n" % str(self.paused)
        output+= "frames...........: %s \n" % self.frames
        output+= "-="*10+'\n'        
        output+= "outputdir........: %s \n" % self.outputdir
        output+= "cachename........: %s \n" % self.cachename
        output+= "cachableNode.....: %s \n" % self.cacheableNode
        output+= "cachedistribution: %s \n" % self.cachedistribution

        return output

#########################################

if __name__ == '__main__':

    mc_job=MayaCacheJob()
    mc_job.scenefile = str(sceneName())
    mc_job.frames = '1-100'
    mc_job.outputdir = '/net/pinot/disk1/tmp/my_cache_dir_3'
    mc_job.cachename = 'myCacheName'
    mc_job.cacheableNode = 'fluidShape2' # the name of the node you want to cache
    mc_job.cachedistribution = 'OneFilePerFrame' # can be 'OneFilePerFrame' or 'OneFile'
    mc_job.makeJobs()

    mc_job.submit()