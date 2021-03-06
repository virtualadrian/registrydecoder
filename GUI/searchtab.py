#
# Registry Decoder
# Copyright (c) 2011 Digital Forensics Solutions, LLC
#
# Contact email:  registrydecoder@digitalforensicssolutions.com
#
# Authors:
# Andrew Case       - andrew@digitalforensicssolutions.com
# Lodovico Marziale - vico@digitalforensicssolutions.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details. 
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA 
#
from errorclasses import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

import datetime

class search_params:

    def __init__(self, searchterms, searchfile, partialsearch, searchKeys, searchNames, searchData, startDate, endDate):

        self.searchterms   = searchterms
        self.searchfile    = searchfile
        self.partialsearch = partialsearch
        self.searchKeys    = searchKeys
        self.searchNames   = searchNames
        self.searchData    = searchData
        self.startDate     = startDate
        self.endDate       = endDate

class searchmatch:

    def __init__(self, match, node, name="", data=""):
        
        self.node  = node
        self.name  = name
        self.data  = data
        self.match = match

    def __cmp__(self, other):
        return self.node == other.node and self.name == other.name and self.data == other.data

    def __eq__(self, other):
        return self.__cmp__(other)

    def hash(self):
        return str(self.node) + str(self.name) + str(self.data)
 
class tmclass:
       
    def __init__(self, report_vals):
 
        self.plugin_set_header = 1
        self.timestamp         = None       
        self.report_data       = report_vals 
   
class searchtab:

    def __init__(self, gui):
        self.name = "Search Tab"
        self.active_tabs = {}

        self.gui = gui

        self.act_handlers = {}

    def draw(self):
        self.fileinfo_hash = self.gcommon.fill_tree(self.gui, "searchTreeWidget")     

    def search_terms_file_browse(self):    
        filename = QFileDialog.getOpenFileName(directory="/home/x/", filter="All (*)", parent=self.gui, caption="Add Search Terms (newline seperated))")            
        
        self.gui.searchTermsLineEdit.setText(filename)

    def boxIsChecked(self, boxName):

        return self.gui.__getattribute__(boxName).isChecked()

    def get_search_params_boxes(self):

        return [self.boxIsChecked("searchKeysCheckBox"), self.boxIsChecked("searchNamesCheckBox"), self.boxIsChecked("searchDataCheckBox")]
       
    def get_search_params(self):

        (searchterms, searchfile)  = self.gcommon.get_search_terms(self.gui)

        if len(searchterms) == 0:
            self.gui.msgBox("No search term(s) were entered. Unable to process")
            return None

        partialsearch  = self.boxIsChecked("partialSearchRadioButton")

        (searchKeys, searchNames, searchData) = self.get_search_params_boxes()

        startDate    = self.gui.searchStartDateLineEdit.text()
        endDate      = self.gui.searchEndDateLlineEdit.text()
    
        if startDate != "":
            s = self.gcommon.parse_date(self, startDate, "start")
        else:
            s = 1
        
        if endDate != "":
           e = self.gcommon.parse_date(self, endDate, "end")
        else:
           e = 1
            
        # input error
        if s == None or e == None:
            ret = None
        else:
            ret = search_params(searchterms, searchfile, partialsearch, searchKeys, searchNames, searchData, startDate, endDate) 
            
        return ret

    # get results for the given search term(s) and fileid
    def do_get_search_results(self, sp, fileid):

        results = []

        # run over all the searchterms in the same file
        for searchterm in sp.searchterms:
            results = results + self.get_search_hits(searchterm, sp.partialsearch, sp.searchKeys, sp.searchNames, sp.searchData)

        # if the user gave a search terms file
        if sp.searchfile != "":
            sp.searchterm = "from %s" % sp.searchfile
        # from the input box
        else:
            sp.searchterm = sp.searchterms[0]

        # remove results that break on the user date filtering
        if len(results) and (sp.startDate or sp.endDate):
            results = self.gcommon.filter_results(self, results, fileid, sp.startDate, sp.endDate)

        return results
    
    # runs the given search term(s) on file id
    def run_search(self, fileid, sp):
    
        (filepath, evi_file, group_name) = self.gcommon.get_file_info(self.fileinfo_hash, fileid)

        self.gui.case_obj.current_fileid = fileid

        # results for fileid
        results = self.do_get_search_results(sp, fileid)

        return self.gcommon.search_results(filepath, evi_file, group_name, results, fileid)

    def get_label_text(self, searchterm, filepath):

        return "Results for searching %s against %s" % (searchterm, filepath)

    def get_tab_text(self, searchterm, is_diff):

        if is_diff:
            ret = "Diff: "
        else:
            ret = ""
        return ret  + "Search Results - %s" % searchterm

    def do_gen_tab(self, sp, sr, fileid, is_diff=0):

        h = self.get_tab_text(sp.searchterm, is_diff)
        l = self.get_label_text(sp.searchterm, sr.filepath)

        return self.gf.generate_search_view_form(self, fileid, h, l, sr.results, is_diff)

    # genereates a search result tab and fills the GUI table
    def generate_tab(self, sp, sr, fileid, color_idxs=[]):

        tab = self.do_gen_tab(sp, sr, fileid)

        (report_vals, match_idxs) = self.get_report_vals(sr.results, fileid)

        self.insert_results(tab, report_vals, match_idxs, sp.searchterm, fileid, color_idxs)
        
        return tab

    # performs the work for a normal (non-diff) search
    # return of None means error
    # return of [] means no search matches
    def run_normal_search(self, sp):

        gen_tab = 0

        all_results = self.gcommon.run_cb_on_tree(self, self.run_search, sp, "searchTreeWidget")

        if all_results == None:
            return

        for results in all_results:

            # generate tab if they are there
            if len(results.results) > 0:
                tab = self.generate_tab(sp, results, results.fileid)
                self.setup_menu(tab.searchResTable)        
                gen_tab = 1

        # alert if no searches matched across all files ran
        if not gen_tab:
            self.gui.msgBox("The given search parameters returned no results.")

    def setup_menu(self, widget):

        self.act_handlers[widget] = self.gcommon.action_handler(self, widget, "Switch to File View", 1, 1)

        self.act_handlers[widget].setup_menu()        

    def get_report_match_info(self, data_ents, fileids):

        report_vals = []
        match_idxs  = []

        for i in xrange(0, len(data_ents)):
            (r, m) = self.get_report_vals(data_ents[i], fileids[i])

            report_vals = report_vals + r
            match_idxs  = match_idxs + m

        return (report_vals, match_idxs)

    def run_diff_search(self, sp):

        # run the searches on the two trees    
        origm  = self.gcommon.run_cb_on_tree(self, self.run_search, sp, "searchTreeWidget", 1)
        newm   = self.gcommon.run_cb_on_tree(self, self.run_search, sp, "searchDiffTreeWidget", 1)

        if origm == None or newm == None:
            return

        # the lists of search matches and their fileids
        (orig_results, orig_fileid) = (origm[0].results, origm[0].fileid)
        (new_results, new_fileid)   = (newm[0].results, newm[0].fileid)

        if orig_results == [] and new_results == []:
            self.gui.msgBox("The given search parameters return no results in either chosen registry hive. Cannot proceed.")
            return

        # the resulting lsits
        (orig_only, new_only, orig_results) = self.gcommon.diff_lists(orig_results, new_results)   
     
        # build the list to be colored
        data_list = orig_only + orig_results + new_only

        # get values to report out of search_match lists
        data_ents = [orig_only, orig_results, new_only]
        fileids   = [orig_fileid, orig_fileid, new_fileid]        

        # idxs to color on
        idxs = self.gcommon.get_idxs(data_ents)

        # will be real values if we decide to report diff output
        sr = self.gcommon.search_results("", "", "", data_list, -42)
        tab = self.do_gen_tab(sp, sr, -42, is_diff=1)
        
        tab.do_not_export = 1
        
        self.gcommon.setup_diff_report(self, tab, orig_only, new_only, orig_results)

        (report_vals, match_idxs) = self.get_report_match_info(data_ents, fileids)
        
        #self.gcommon.hide_tab_widgets(tab)

        self.insert_results(tab, report_vals, match_idxs, sp.searchterm, -42, idxs)

    # called when 'search' is clicked
    def viewTree(self):

        sp = self.get_search_params()

        if not sp or sp == None:
            return

        perform_diff = self.gui.performSearchDiffCheckBox.isChecked()

        if perform_diff:
            self.run_diff_search(sp)   
           
        # normal search
        else:
            self.run_normal_search(sp)

        # to catch anyone pulling the stale file id
        self.gui.case_obj.current_fileid = -42

    def handle_search_delete(self, event):

        curtab = self.gui.analysisTabWidget.currentWidget()
        
        self.gui.case_obj.current_fileid = curtab.fileid
        
        table  = curtab.searchResTable

        if event.key() == Qt.Key_Delete:
            self.remove_search_result(curtab, table)
        
        return QTableWidget.keyPressEvent(table, event)

    def remove_search_result(self, curtab, table):

        row = table.currentRow()        

        table.removeRow(row)       

    # gets all the search hits into a list of searchmatch objects
    def get_search_hits(self, searchterm, partialsearch, searchKeys, searchNames, searchData):
        
        matches = []

        if searchKeys:
           
            nodes = self.tapi.node_searchfor(searchterm, partialsearch)

            for node in nodes:
                matches.append(searchmatch(0, node))  
   
        if searchNames:
            
            nodevals = self.tapi.names_for_search(searchterm, partialsearch)

            for nodeval in nodevals:
                
                matches.append(searchmatch(1, nodeval.node, nodeval.name, nodeval.data))
            
        if searchData:
            
            nodevals = self.tapi.data_for_search(searchterm, partialsearch)

            for nodeval in nodevals:
                matches.append(searchmatch(2, nodeval.node, nodeval.name, nodeval.data))
            
        return matches

    def get_report_vals(self, results, fileid):

        match_idxs = []
        ret = []

        for row in xrange(len(results)):
            
            r = results[row]
            
            lastwrite = r.node.timestamps[fileid]
            lastwrite = datetime.datetime.fromtimestamp(lastwrite).strftime('%Y/%m/%d %H:%M:%S')
 
            vals  = [lastwrite, r.node.fullpath, r.name, r.data]

            match_idxs.append(r.match+1)

            ret.append(vals)

        return (ret, match_idxs)

    # puts rows into GUI table and keeps records for reporting and switching views
    def insert_results(self, tab, report_vals, match_idxs, searchterm, fileid, color_idxs):

        report = self.rm.display_reports[0]
        
        tab.tblWidget = tab.searchResTable

        headers = ["Last Write Time", "Key", "Name", "Data"]
        report_vals = [headers] + report_vals
        
        tm = tmclass(report_vals)
        
        self.rm.report_tab_info(report, tm, tab, self.active_tabs, fileid, "Search", "Search Term", "Diff: " + searchterm, match_idxs=match_idxs, color_idxs = color_idxs)

    def createReportClicked(self): 
        self.rh.createReportClicked("Search Single")
    
    def diffBoxClicked(self, isChecked):
        self.gcommon.diffBoxClicked(self, isChecked, "searchDiffTreeWidget")

