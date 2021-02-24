import json
import sqlite3
from random import random

import bqa.player as player

class QTable:

    def __init__(self, db='table.db', size=64, quantum=32):
        '''Returns a new instance of a QTable configured with
        the specified DB, SIZE and QUANTUM.

        Args:
            db (str): The name of the backing sqlite database.
            size (int): The max number of entries to cache.
            quantum (int): The number of accesses before each
            entries age is reset to 0.

        Returns:
            (QTable): A QTable instance.
        '''
        # this table maps states to weights/biases/ages
        self._table = dict()
        self._db = sqlite3.connect(db)
        self._connected = True
        self._size = size
        self._quantum = quantum
        self._n = 0
        self._create_db()


    def __len__(self):
        return len(self._table)


    def _age(self):
        '''Ages each entry in the qtable cache by 1. Will reset
        the age of each entry to 0 each time the quantum is
        reached.
        '''
        for key, value in self._table.items():
            weights, biases, qvalues, age = value[0], value[1], value[2], value[3]
            if self._n % self._quantum:
                age = 0
            self._table[key] = [weights, biases, qvalues, age + 1]
        self._n += 1


    def _create_db(self):
        cursor = self._db.cursor()
        cursor.execute('create table if not exists qtable (state_hash int primary key, weights text, biases text, qvalues text)')
        self._db.commit()


    def _evict(self):
        max_age = -1
        max_state_hash = None
        max_weights = None
        max_biases = None
        max_qvalues = None
        # if multiple elements have the same largest age, the
        #  last element will be evicted
        for key, value in self._table.items():
            weights, biases, qvalues, age = value[0], value[1], value[2], value[3]
            if age > max_age:
                max_age = age
                max_state_hash = key
                max_weights = weights
                max_biases = biases
                max_qvalues = qvalues
        # write out the state, weights, biases
        self._write_entry(max_state_hash, max_weights, max_biases, max_qvalues)
        del self._table[max_state_hash]


    def _read_entry(self, state_hash):
        cursor = self._db.cursor()
        try:
            weights, biases, qvalues = cursor.execute('select weights, biases, qvalues from qtable where state_hash=?', (state_hash,))
        except ValueError:
            return None
        return json.loads(weights), json.loads(biases), json.loads(qvalues)


    def _write_entry(self, state_hash, weights, biases, qvalues):
        weights = json.dumps(weights)
        biases = json.dumps(biases)
        qvalues = json.dumps(qvalues)
        cursor = self._db.cursor()
        cursor.execute('insert into qtable values (?, ?, ?, ?) on conflict(state_hash) do update set weights=?, biases=?, qvalues=?', (state_hash, weights, biases, qvalues, weights, biases, qvalues,))
        self._db.commit()


    def contains(self, state):
        state_hash = hash(tuple(state.values()))
        return state_hash in self._table


    def get(self, state):
        state_hash = hash(tuple(state.values()))
        if state_hash in self._table: 
            weights, biases, qvalues, _ = self._table[state_hash]
            self._table[state_hash] = [weights, biases, qvalues, 0]
            return [weights, biases, qvalues]
        db_result = self._read_entry(state_hash)
        if db_result is None:
            game_stage = state['game_stage']
            if game_stage == player.Agent.PRE_ROUND:
                weights = [random(), random()]
                biases = [random(), random()]
                qvalues = [1, 0]
                if self.__len__() == self._size:
                    self._evict()
                self._table[state_hash] = [weights, biases, qvalues, 0]
                return [weights, biases, qvalues]
            else:
                weights = [random(), random(), random()]
                biases = [random(), random(), random()]
                qvalues = [0, 0, 0]
                if self.__len__() == self._size:
                    self._evict()
                self._table[state_hash] = [weights, biases, qvalues, 0]
                return [weights, biases, qvalues]
        weights, biases, qvalues = db_result[0], db_result[1], db_result[2]
        if self.__len__() == self._size:
            self._evict()
        self._table[state_hash] = [weights, biases, qvalues, 0]
        return [weights, biases, qvalues]


    def init_table(self, db):
        '''Initializes a new table.

        Args:
            db (str): The name of the database to initialize.
        '''
        self.load_db(db)
        self._create_db(db)


    def load_table(self, db):
        '''Loads a table from a sqlite file. Ues this to switch
        between tables.

        Args:
            db (str): The name of the sqlite database to connect
            to that stores the table you want to load.
        '''
        if self._connected:
            self._db.close()
        self._db = sqlite.connect(db)
        self._table.clear()
        self._n = 0
        

    def put(self, state, weights, biases, qvalues):
        '''Stores STATE in the QTable cache such that it's
        weights=WEIGHTS, biases=BIASES, qvalues=QVALUES and 
        age=0. If STATE is not already in the table, this 
        function evicts a cache entry if the cache is full 
        and writes STATE and it's accompanying values to the 
        cache.

        Args:
            state (int): A state hash representing the state
            to map against.
            weights (list): A list of floating point numbers
            representing the weights for each action.
            biases (list): A list of floating point numbers 
            representing the biases for each action.
            qvalues (list): A list of floating point numbers 
            representing the qvalues for each action.
        '''
        state_hash = hash(tuple(state.values()))
        if state_hash not in self._table:
            if self.__len__() == self._size:
                self._evict()
        self._table[state_hash] = [weights, biases, qvalues, 0]


    def save_table(self):
        '''Saves the agent's qtable to file.'''
        for key, value in self._table.items():
            state_hash = key
            weights, biases, qvalues = value[0], value[1], value[2]
            self._write_entry(state_hash, weights, biases, qvalues)
        if self._connected:
            self._db.close()
