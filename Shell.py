
from subprocess import call,PIPE
import sys,os
import logging

class Shell(object):
    """Base Shell class for gathering shell environment information"""

    class Editor(BB):
           """Editor window class for editing the interactive configs"""
           def __init__(self):
               super(Editor, self).__init__()
               
    
    def __init__(self):
        super(Shell, self).__init__()
        self.GDI = None
        self.env={}
        self.err=sys.stderr
        self.out=sys.stdout

    def getConnection(self):
        """Return the GDI connection instance"""
        raise NotImplementedError,"Shell.getConnection()"

    def getErr(self):
        """get the error output writer, for redirecting any error output to, by default this is sys.stderr"""
        return self.err if self.err != None else sys.stderr

    def getOut(self):
        """get the stadard output writer, for redirecting any standard output to, by default this is sys.stdout"""
        return self.out if self.out != None else sys.stdout

    def getLogger(self):
        """return the logger instance if it exists ready for logging command output"""

    def getEnv(self):
        """Set this shells environment to the current session os.envion dictionary"""
        self.env = dict(os.environ)
        return self.env

    def setEnv(self,**args):
        """set an environment varable(s), key=value become environment:value, can have multiple entries"""
        for k,v in args.items():
            self.env[k]=v


class AbstractCommand(object):
    """Base commad class used to create and run commandline applications, this class is inherited by other command classes"""
    def __init__(self,shell=None):
        super(AbstractCommand, self).__init__()

        if not isinstance(shell,Shell):
            self.shell = Shell()
        else:
            self.shell = shell

        self.gdi = None # pointer to GDI interface instance (not implimented yet)
        self.commad = "ls"
        self.exit_code = 0
        self.out = ""
        self.err = ""

    @classmethod
    def run(self,**args):
        """run the given arguments in the shell"""
        
        _cmd = [self.command]
        for a,v in args: # needs a little clean-up and sanity check happening here
            _cmd += a
            _cmd += v

        call(_cmd,stdout=self.shell.out,stderr=slef.shell.err)

    @classmethod
    def getExitCode(self):
        """Return the exit status of this command"""
        return self._exit_code

    @classmethod
    def setExitCode(self,code):
        """Return the exit status of this command"""
        self._exit_code = code
        return self._exit_code

    @classmethod
    def getUsage(self):
        """Return the usage stringfor the command"""
        return ""

    @classmethod
    def printCommand(self):
        """Print the command that was ran to stdout"""
        print self._cmd
    
    @classmethod
    def function(self):
        pass

class QConfOptions(object):
    """QConfOptions object for convienence of setting and editing the commandline arguments of the QConfCommand Class"""

    args = {}



class QConfCommand(AbstractCommand):
    """
    QConfCommand class for running configuration querys and commands
    """
    def __init__(self):
        super(QConfCommand, self).__init__()
    
    def addAdminHost(self,options):
        _args={}
    
    def addSubmitHost(self,options):
        pass
    
    def addCalendar(self):
        pass
    
    def addOperator(self):
        pass
    
    def addManager(self):
        pass
    
    def addHostgroup(self):
        pass
    
    def addConfiguration(self):
        pass
    
    def addCheckpoint(self):
        pass
    
    def addUserSet(self):
        pass
    
    def addShareTree(self):
        pass
    
    def addExecHost(self):
        pass
    
    def modifyComplexEntry(self):
        pass
    
    def modifyComplexEntryFromFile(self):
        pass
    
    def modifyShareTree(self):
        pass
    
    def modifyShareTreeFromFile(self):
        pass
    
    def modifyExecHost(self):
        pass
    
    def modifyResourceQuotaSet(self):
        pass
    
    def cleanQueue(self):
        pass
    
    def clearUsage(self):
        pass
    
    def deleteAdminHost(self, oi):
        pass 
           
    def deleteAttribute(self, oi):
        pass 
           
    def deleteManager(self, oi):
        pass 
           
    def deleteOperator(self, oi):
        pass 
           
    def deleteShareTree(self, oi):
        pass 
           
    def deleteSubmitHost(self, oi):
        pass 
           
    def deleteUserSet(self, oi):
        pass 
           
    def deleteUserSetList(self, oi):
        pass
    
    def showClusterQueue(self, oi):
        pass 
           
    def showComplexEntry(self, oi):
        pass 
           
    def showConfiguration(self, oi):
        pass 
           
    def showDetachedSettings(self, oi):
        pass 
           
    def showEventClientList(self, oi):
        pass 
           
    def showHostgroupResolved(self, oi):
        pass 
           
    def showHostgroupTree(self, oi):
        pass 
           
    def showParallelEnvironment(self, oi):
        pass 
           
    def showProcessors(self, oi):
        pass 
           
    def showProject(self, oi):
        pass 
           
    def showResourceQuotaSet(self, oi):
        """Implements qconf -srqs option"""
        pass 
          
    def showSchedulerState(self, oi):
        pass 
           
    def showShareTree(self, oi):
        pass 
           
    def triggerSchedulerMonitoring(self, oi):
        pass 


class QModCommand(AbstractCommand):
    """Wrapper class for qmod command line"""
    def __init__(self, arg):
        super(QModCommand, self).__init__()
        self.arg = arg
        
    def parseJobList(self,arg):
        pass
           
    def parseJobWCQueueList(self,arg): 
        pass
           
    def parseWCQueueList(self, arg):
        pass
        
class QHostCommand(AbstractCommand):
    """Wrapper command for qgost command line program"""
    def __init__(self, **args):
        super(QHostCommand, self).__init__()
        self.args = args

    def function(self):
        pass
        