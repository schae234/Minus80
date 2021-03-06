#!/usr/bin/env python3
import tempfile
import re

import apsw as lite
import os as os
import numpy as np
import pandas as pd
import bcolz as bcz


# Suppress the warning until the next wersion
import blaze as blz

from .Config import cf
from apsw import ConstraintError


class Freezable(object):

    '''
    Freezable is an abstract class. Things that inherit from Freezable can
	be loaded and unloaded from the Minus80.

	A freezable object is a persistant object that lives in a known directory
    aimed to make expensive to build objects and databases loadable from 
    new runtimes.
    
    The three main things that a Freezable object supplies are:
    - access to a sqlite database (relational records)
    - access to a bcolz databsase (columnar data)
    - access to a key/val store
    - access to named temp files

    '''

    def __init__(self, name, type=None, basedir=None):
        # Set up our base directory
        if basedir == None:
            self._m80_basedir = cf.options.basedir
        self._m80_name = name
        # 
        if type == None:
            # Just use the class type as the type
            self._m80_type = re.match(
                "<class '(.+)'>",
                str(self.__class__)
            ).groups()[0]
        # A dataset already exists, return it
        self._db = self._open_db(self._m80_name)

        try:
            cur = self._db.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS globals (
                    key TEXT,
                    val TEXT,
                    type TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS uniqkey ON globals(key)
                ''')
        except TypeError:
            raise TypeError('{}.{} does not exist'.format(type, name))

    def _open_db(self, dbname, type=None):
        '''
        This is the access point to the sqlite database
        '''
        # This lets us grab databases for other types
        if type is None:
            type = self._m80_type
        # return a connection if exists
        return lite.Connection(
            os.path.expanduser(
                os.path.join(
                    self._m80_basedir,
                    'databases',
                    "{}.{}.db".format(type, dbname)
                )
            )
        )

    def _bcolz(self, tblname, dbname=None, type=None, df=None, blaze=False):
        '''
        This is the access point to the bcolz database
        '''
        if type is None:
            type = self._m80_type
        if dbname is None:
            dbname = self._m80_name
        if df is None:
            # return the dataframe if it exists 
            try:
                df = bcz.open(
                    os.path.expanduser(
                        os.path.join(
                            cf.options.basedir,
                            'databases',
                            "{}.{}.{}".format(type, dbname, tblname)
                        )
                    )
                )
            except IOError:
                return None
            else:
                if len(df) == 0:
                    df = pd.DataFrame()
                    if blaze:
                        df = blz.data(df)
                else:
                    if blaze:
                        df = blz.data(df)
                    else:
                        df = df.todataframe()
                if not blaze and 'idx' in df.columns.values:
                    df.set_index('idx', drop=True, inplace=True)
                    df.index.name = None
                return df
        
        else:
            if not(df.index.dtype_str == 'int64') and not(df.empty):
                df = df.copy()
                df['idx'] = df.index
            if isinstance(df,pd.DataFrame):
                path = os.path.expanduser(
                        os.path.join(
                            cf.options.basedir,
                            'databases',
                            "{}.{}.{}".format(type, dbname, tblname)
                        )
                    )
                if df.empty:
                    bcz.fromiter((),dtype=np.int32,mode='w',count=0,rootdir=path)
                else:
                    bcz.ctable.fromdataframe(df,mode='w',rootdir=path)
                
            if 'idx' in df.columns.values:
                del df
            return
    
    def _tmpfile(self):
        # returns a handle to a tmp file
        return tempfile.NamedTemporaryFile(
            dir=os.path.expanduser(
                os.path.join(
                    cf.options.basedir,
                    "tmp"
                )   
            )
        )

    def _dict(self, key, val=None):
        '''
            Stores global variables for the freezable object
        '''
        try:
            if val is not None:
                val_type = type(val)
                val = str(val)
                if val_type not in ('int','float','str'):
                    raise TypeError(
                        'val must be in [int,float,str], not {}'.format(val_type)
                    )
                self._db.cursor().execute('''
                    INSERT OR REPLACE INTO globals
                    (key, val, type)VALUES (?, ?, ?)''', (key, val, type)
                )
            else:
                return self._db.cursor().execute(
                    '''SELECT val FROM globals WHERE key = ?''', (key, )
                ).fetchone()[0]
        except TypeError:
            raise ValueError('{} not in database'.format(key))
