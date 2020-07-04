#!/usr/bin/env python3
import asyncio
from random import randint


from constants import TIME
from tools.arff import Arff
# from tools.analyzer import Analyzer
from tools.errors import CollectionError


class Collection:
    # Data Types
    INTEGER  = 'int'
    STRING   = 'string'
    REAL     = 'real'
    VALUE_NA = '?'

    # Window Defaults
    WINDOW_SIZE    = 50
    WINDOW_OVERLAP = 25

    def __init__(self, name, data=[], attr_names=[], attr_types=[],
                 window_size=WINDOW_SIZE,
                 window_overlap=WINDOW_OVERLAP,
                 analyzer=None):
        self.name           = name
        self.data           = data
        self.attr_names     = attr_names
        self.attr_types     = attr_types
        self.window_size    = window_size
        self.window_overlap = window_overlap
        self.analyzer       = analyzer

    def import_data(self, filename):
        a = Arff(arff=filename)
        self.data.extend(a[:, :])
        self.attr_names = a.attr_names.copy()
        self.attr_types = a.attr_types.copy()

    def get_entry_by_value(self, feature_names, values):
        # Ensure that both metadata and value to filter by is sent
        if len(feature_names) != len(values):
            return None

        for i in range(len(feature_names)):
            name = feature_names[i]
            value = values[i]
            if name not in self.attr_names:
                return None
        
    async def add_entry(self, data):
        entry = []
        for i in range(len(self.attr_names)):
            name = self.attr_names[i]
            type = self.attr_types[i]
            if name in data and (type == self.REAL and isinstance(data.get(name), float)):
                entry.append(float(data.get(name)))
            elif name in data and (type == self.INTEGER and isinstance(data.get(name), int)):
                entry.append(int(data.get(name)))
            elif name in data and type == self.STRING:
                entry.append(data.get(name))
            elif type == self.REAL or type == self.INTEGER:
                print('unable to enter value {} for name {}'.format(data.get(name), name))
                entry.append(float('nan'))
            else:
                entry.append(self.VALUE_NA)
        self.data.append(entry)

        # Analyze latest window if ready
        if len(self.data) % self.window_overlap == 0 and \
            len(self.data) >= self.window_size:
            analysis = await self.analyze_window(start=(-1*self.window_size))

        # Not ready yet, don't return anything
        else:
            analysis = None

        return analysis

    def write_to_file(self, filename, append=False):        
        if append:
            f = open(filename, 'a')
        else:
            f = open(filename, 'w')

        f.write('@relation {}\n'.format(self.name))
        for i in range(len(self.attr_names)):
            f.write('@attribute {} {}\n'.format(self.attr_names[i],
                                                self.attr_types[i]))

        f.write('@data\n')
        f.write('%\n% {} instances\n%\n')
        for entry in self.data:
            for value in entry[:-1]:
                f.write('{},'.format(value))
            f.write('{}\n'.format(entry[-1]))
        f.write('%\n%\n%')
        f.close()

    async def analyze_all(self, window_size=None, window_overlap=None):
        analysis = []
        # Use initialized window_overlap if not overridden
        if window_overlap is not None and isinstance(window_overlap, int):
            bo = window_overlap
        else:
            bo = self.window_overlap
        
        # Use initialized window_size if not overridden
        if window_size is not None and isinstance(window_size, int):
            bs = window_size
        else:
            bs = self.window_size

        for i in range(len(self.data) // bo):
            start = i * bs
            end = start + bs

            # Only analyze full windows
            if end >= len(self.data):
                break
            analysis.append(self.analyze_window(start, end))
        return analysis

    async def analyze_window(self, start=0, end=-1):
        window = self.data[start:end]
        
        # TODO: Send window to be analyzed by ML & generate report
        # Placeholder analysis that randomly selects "not jump" or "Lutz"
        labels = ['Lutz', 'not jump', 'not jump']
        idx = randint(0, 9) % len(labels)

        analysis = {
            'name': self.name,
            'value': labels[idx],
            'session': window[0][1],
            'athlete': window[0][0],
            'start': window[0][3],
            'end': window[-1][3]}

        return analysis

    def __str__(self):
        s = '__{}__\n'.format(self.name)
        s += 'attributes: ['
        for i in range(len(self.attr_names) - 1):
            if i < len(self.attr_types):
                s += '{}({})'.format(self.attr_names[i], self.attr_types[i])
            else:
                s += '{}'.format(self.attr_names[i])
            s += ','
        if i < len(self.attr_types):
            s += '{}({})]\n'.format(self.attr_names[i], self.attr_types[i])
        else:
            s += '{}]\n'.format(self.attr_names[i])
        
        s += 'data:\n{}'.format(self.data)
        return s
