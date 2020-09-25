# Copyright (C) 2019 h0bB1T
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
#
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import bpy, bpy.utils.previews, os

class CollectionList:
    """
    Stores all information about a single collection. The parser is used
    to parse a new list based on the data. The structure of "data" is parser specific.
    """
    def __init__(self, parser, data):
        self.parser = parser
        self.data = data
        self.mustScan = True
        self.collection = None
        self.items = []


    def reset(self):
        """
        Delete items and collection (if allocated).
        """
        self.items.clear()
        if self.collection:
            bpy.utils.previews.remove(self.collection)


class PreviewHelper:
    """
    Helper class to manage the lifecycle of different preview items. Able to reparse
    using a parser.
    """
    collections = {}

    @staticmethod
    def addCollection(name, parser, data):
        """
        Add a new collection, identified by "name". The parser is used to build
        the item list using the given data.
        """
        PreviewHelper.collections[name] = CollectionList(parser, data)


    @staticmethod
    def scanCollection(lst):
        """
        Scans the items according to parser and the current data.
        """
        lst.mustScan = False
        lst.reset()
        lst.parser.parse(lst)


    @staticmethod
    def getCollection(name):
        """
        Return the collection identified by name. If outdated (by default), parse it.
        """
        lst = PreviewHelper.collections[name]
        if lst.mustScan:
            PreviewHelper.scanCollection(lst)
        return lst


    @staticmethod
    def getDynamicCollection(name, parser, data):
        if name not in PreviewHelper.collections:
            PreviewHelper.collections[name] = CollectionList(parser, data)

        lst = PreviewHelper.collections[name]
        if lst.data != data:
            lst.data = data
            lst.mustScan = True

        if lst.mustScan:
            PreviewHelper.scanCollection(lst)
            
        return lst


    @staticmethod
    def setData(name, data, forceUpdate=False):
        """
        Adjust data for collection, may result in reparsing.
        """
        lst = PreviewHelper.collections[name]
        if lst.data != data or forceUpdate:
            lst.data = data
            lst.mustScan = True


    @staticmethod
    def forceUpdate(name):
        """
        Force update for specific collection.
        """
        PreviewHelper.collections[name].mustScan = True


    @staticmethod
    def removeAllCollections():
        """
        Cleanup method, removes all collections.
        """
        for lst in PreviewHelper.collections.values():
            lst.reset()
        PreviewHelper.collections.clear()
