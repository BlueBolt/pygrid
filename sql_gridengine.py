
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
GRID Engine SQL database module

provides interfaces for :
    
    MySQL
    PostgreSQL

'''

import Database 

from sqlalchemy import create_engine, MetaData, Table,Column, Integer, String
from sqlalchemy.orm import sessionmaker,column_property,mapper,clear_mappers
from sqlalchemy.ext.declarative import declarative_base

from config_gridengine import get_config

def sql_connect():
    
    cfg_data = get_config()
    
    settings = {'sql_type':'mysql',
                'sql_server':'localhost',
                'sql_port':'3306',
                'sql_user':'Anonymous',
                'sql_password':'',
                'sql_database':'grid'}    
    
    for key in settings.keys():
        if cfg_data.has_option('SQL',key):
            settings[key]=cfg_data.get('SQL',key)
        
    # MySQL
    if settings['sql_type'] == 'mysql':
        
        db=Database.Connection(settings['sql_server'],
                                 settings['sql_database'],
                                 settings['sql_user'],
                                 settings['sql_password'])
                
        return db
    
    else:
        return None

 

def alchemy_connect():
    
    cfg_data = get_config()
    
    settings = {'sql_type':'mysql','sql_server':'localhost','sql_port':'3306','sql_user':'Anonymous','sql_password':'','sql_database':'grid'}    
    
    for key in settings.keys():
        if cfg_data.has_option('SQL',key):
            settings[key]=cfg_data.get('SQL',key)
            
    e_str = '%(sql_type)s://%(sql_user)s:%(sql_password)s@%(sql_server)s:%(sql_port)s/%(sql_database)s' % settings
    
    engine = create_engine(e_str)
    
    Base = declarative_base(engine)  
    
    metadata = Base.metadata
    
    metadata.reflect(engine)
    
    Session = sessionmaker(bind=engine)
    
    session = Session()
    
    return session

def findJobData(table,**filters):
    """
    Query the grid database for jobs that match any filters given by **args

    e.g. 

    Return all the Jobs that we submitted by user 'fred' or type arnold:

    job_list = findJobData('SHOW_myShow',{user:'fred',type:'arnold'})

    """


    s = alchemy_connect()

    en = s.get_bind(mapper=None)

    metadata = MetaData(en)

    lwtf_table = Table('SHOW_lwtf',metadata, autoload=True)
    tp_table = Table('SHOW_tp_poirot',metadata, autoload=True)

    class SHOW_TABLE(object):
      pass

    mapper(SHOW_TABLE,tp_table)

    if len(filters):

        filters_as_args = list()
        for key,value in filters.items():
            filters_as_args.append( '%s="%s"'%(key,value) ) 

        return eval( "s.query(SHOW_TABLE).filter_by(%s).all()"%','.join(filters_as_args) )

    else:

        return s.query(SHOW_TABLE).all()

    
