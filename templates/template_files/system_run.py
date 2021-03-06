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
#
#
#


pluginname = "System Runs"
description = "Displays (some of the) programs that run at system startup."
hive = "SOFTWARE"    
documentation = ""
    

def run_me():

    run_keys = (
        "\Microsoft\Windows\CurrentVersion\Runonce",  
        "\Microsoft\Windows\CurrentVersion\policies\Explorer\Run",  
        "\Microsoft\Windows\CurrentVersion\Run" )  

    reg_set_report_header(("Name", "Path"))

    for rk in run_keys:
        regkey = reg_get_key(rk)
        if regkey:
            reg_report_values_name_data(regkey)





