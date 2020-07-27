import os
import sys
import os.path
import collections
import subprocess
import threading
import time
import json
import base64
import binascii
import tkinter as tk
import tkinter.ttk as ttk
import winsound
import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog

try: 
    import queue
except ImportError:
    import Queue as queue

from app_android_adb_server import ADB
from app_genymotion_shell import GenyShell
from app_test_executor import AndroidAutomator

class TabTest(tk.Frame):
    def __init__(self, parent):
        if parent is not None:
            tk.Frame.__init__(self, parent.nTabs)
        else:
            tk.Frame.__init__(self, None)
        self.parent = parent
        self.label = "Testing"
        self.sceneList = [] # Scenes
        self.adb = ADB()
        self.genyShell = GenyShell()
        self.list_of_connected_devices = {}
        self.installedApps = {}
        self.selected_device = None
        
        if parent is not None:
            parent.nTabs.add(self, text = self.label)
        
        self.grid_columnconfigure(0, weight = 1, minsize = 150)
        self.grid_columnconfigure(1, weight = 1, minsize = 150)
        self.grid_columnconfigure(2, weight = 1, minsize = 300)
        self.buttons = []
        self.rootDir = os.getcwd()() if self.parent == None else self.parent.rootDir
        
        self.device_tabs = {}
        
        self.genymotionSupported = False
        
        self.buildGUI()
        
    # Run Game Parameters
    def buildGUI(self):
        # Turn on adb mode in tcpip mode
        commandParams = ["tcpip", 5555]
        self.adb.process_args(commandParams)
    
        # Devices
        self.adbDevicesResult = self.adb.call("devices", self.adb.devices);
        self.deviceOSVersions = {}
        self.adb_devices_counter = 0;
        # self.adb.get_sd_free_space()
        if isinstance(self.adbDevicesResult, list):
            if len(self.adbDevicesResult) > 1:
                for x in range(len(self.adbDevicesResult)):
                    if len(self.adbDevicesResult[x]) > 0:
                        value = self.adbDevicesResult[x]
                        self.list_of_connected_devices[value] = x
                        self.adb_devices_counter += 1
            else:
                if len(self.adbDevicesResult) > 0:
                    self.list_of_connected_devices[self.adbDevicesResult[0]] = 1
                    self.adb_devices_counter += 1
                    
        if self.genymotionSupported:
            commandParams = ["devices"]
            self.genyShell.process_args(commandParams)
            gennyDevicesResult = self.genyShell.devices_info
            for key, value in gennyDevicesResult.items():
                print("Found Device: " + key)
                print("Info ----->")
                gennyDevicesResult[key].printInfo()
                self.adb_devices_counter += 1
                self.list_of_connected_devices[key] = self.adb_devices_counter
        
        self.lDevices = tkinter.LabelFrame(self, text = "Devices", padx = 5, pady = 5)
        self.lDevices.grid(column = 0, row = 0, columnspan = 2, rowspan = 4, sticky = "NSWE", padx = 5, pady = 5)
        
        self.bRefreshDevices = tkinter.Button(self.lDevices, text = "Refresh", padx = 5, command = self.refresh_devices)
        self.bRefreshDevices.grid(column = 3, row = 0, sticky = "WNSE", pady=3)
        
        self.bAddDevice = tkinter.Button(self.lDevices, text = "Add Device", padx = 5, command = self.add_device_for_testing)
        self.bAddDevice.grid(column = 4, row = 0, sticky = "WNSE", pady=3)
        
        self.bRemoveDevice = tkinter.Button(self.lDevices, text = "Remove Device", padx = 5, command = self.remove_device_from_testing)
        self.bRemoveDevice.grid(column = 5, row = 0, sticky = "WNSE", pady=3)
        
        self.lblSvnAddress = tkinter.Label(self.lDevices, text = "Selected Devices for Test: ")
        self.lblSvnAddress.grid(row = 2, column = 0, sticky = "W")
        
        self.testingDevicesView = tkinter.ttk.Treeview(self.lDevices, selectmode = tkinter.EXTENDED, height = 10, show=["tree"])
        scrollBarY = tkinter.ttk.Scrollbar(self.lDevices, orient = tkinter.VERTICAL, command=self.testingDevicesView.yview)
        scrollBarX = tkinter.ttk.Scrollbar(self.lDevices, orient = tkinter.HORIZONTAL, command=self.testingDevicesView.xview)
        scrollBarY.grid(row = 3, column = 2, sticky = "ns")
        scrollBarX.grid(row = 5, column = 0, sticky = "ew", columnspan = 2)
        self.testingDevicesView.configure(yscroll=scrollBarY.set, xscroll=scrollBarX.set)
        self.testingDevicesView.column("#0", width = 100)
        self.testingDevicesView.grid(row = 3, column = 0, columnspan = 2, sticky = "ENWS")
        
        self.cbDevices = tkinter.ttk.Combobox(self.lDevices, state = "readonly", textvariable = self.list_of_connected_devices, width = 25)
        self.cbDevices.config(values = [""] + list(self.list_of_connected_devices.keys()))
        self.cbDevices.bind("<<ComboboxSelected>>", self.on_device_selected)
        self.cbDevices.grid(column = 0, row = 0, columnspan = 2, sticky = "N")
        self.cbDevices.set("")
        
        # self.lfApplicationUtils = tk.LabelFrame(self, text="Application Scripts", padx = 5, pady = 5)
        # self.lfApplicationUtils.grid(column = 2, row = 0, sticky = 'NEWS', padx = 5, pady = 5)
        # self.lfApplicationUtils.grid_columnconfigure(0, weight = 1)
        # self.lfApplicationUtils.grid_columnconfigure(1, weight = 1)
        
        self.lDeploymentFiles = tkinter.LabelFrame(self, text = "Test Files", padx = 5, pady = 5)
        self.lDeploymentFiles.grid(row=0, column = 2, rowspan = 2, sticky = "NSWE", padx = 5, pady = 5)
        self.lApkFilePathStr = ""
        self.lApkFilePath = tkinter.Label(self.lDeploymentFiles, text="APK File: ").grid(row = 1)
        self.tApkFilePath = tkinter.Text(self.lDeploymentFiles, height = 1, width = 40)
        self.tApkFilePath.tag_configure("center", justify="center")
        self.tApkFilePath.tag_add("center", 1.0, "end")
        self.tApkFilePath.insert("end", self.lApkFilePathStr)
        self.tApkFilePath.configure(state = "disabled")
        self.tApkFilePath.grid(column = 1, row = 2, sticky = "WN", pady = 5)
        
        self.bApkFileSearch = tkinter.Button(self.lDeploymentFiles, text = "Search",	padx = 5, command = self.serachForApk)
        self.bApkFileSearch.grid(column = 2, row = 2, columnspan = 2, sticky = "WN", pady = 5)
        
        self.lObbFilePathStr = ""
        self.lObbFilePath = tkinter.Label(self.lDeploymentFiles, text="Obb File: ").grid(row = 5)
        self.tObbFilePath = tkinter.Text(self.lDeploymentFiles, height = 1, width = 40)
        self.tObbFilePath.tag_configure("center", justify="center")
        self.tObbFilePath.tag_add("center", 1.0, "end")
        self.tObbFilePath.insert("end", self.lObbFilePathStr)
        self.tObbFilePath.configure(state = "disabled")
        self.tObbFilePath.grid(column = 1, row = 5, sticky = "WN", pady = 5)
        
        self.bObbFileSearch = tkinter.Button(self.lDeploymentFiles, text = "Search",	padx = 5, command = self.searchForObb)
        self.bObbFileSearch.grid(column = 2, row = 5, columnspan = 2, sticky = "WN", pady = 5)
        
        self.lTestCommandStr = ""
        self.lTestCommand = tkinter.Label(self.lDeploymentFiles, text="Test Command: ").grid(row = 7)
        self.tTestCommand = tkinter.Text(self.lDeploymentFiles, height = 1, width = 40)
        self.tTestCommand.tag_configure("center", justify="center")
        self.tTestCommand.tag_add("center", 1.0, "end")
        self.tTestCommand.insert("end", self.lTestCommandStr)
        self.tTestCommand.configure(state = "disabled")
        self.tTestCommand.grid(column = 1, row = 7, sticky = "WN", pady = 5)
        
        self.bTestFileSearch = tkinter.Button(self.lDeploymentFiles, text = "Search",	padx = 5, command = self.searchForTest)
        self.bTestFileSearch.grid(column = 2, row = 7, columnspan = 2, sticky = "WN", pady = 5)
        
        
        self.bRunTest = tkinter.Button(self.lDeploymentFiles, text = "Run Test",	padx = 5, command = self.runTests)
        self.bRunTest.grid(column = 1, row = 8, columnspan = 2, sticky = "WN", pady = 5)
        
        # Run Game
        # self.lfApplicationUtils = tk.LabelFrame(self, text="Application Scripts", padx = 5, pady = 5)
        # self.lfApplicationUtils.grid(column = 2, row = 0, sticky = 'NEWS', padx = 5, pady = 5)
        # self.lfApplicationUtils.grid_columnconfigure(0, weight = 1)
        # self.lfApplicationUtils.grid_columnconfigure(1, weight = 1)
        
    def create_btn(self, mode): 
        cmd = lambda: self.list.config(selectmode=mode) 
        return tk.Button(self, command=cmd, 
                         text=mode.capitalize()) 
                         
    def serachForApk(self, event = None):
        self.dir_opt = options = {}
        options["initialdir"] = os.getcwd()
        options["mustexist"] = False
        options["parent"] = self.lDeploymentFiles
        options["title"] = "Search:"
        self.tApkFilePath.configure(state = "normal")
        self.tApkFilePath.delete("1.0", "end")
        self.lApkFilePathStr = tkinter.filedialog.askopenfilename()
        self.tApkFilePath.insert("end", self.lApkFilePathStr)
        self.tApkFilePath.configure(state = "disabled")
        
    def searchForTest(self, event = None):
        self.dir_opt = options = {}
        options["initialdir"] = os.getcwd()
        options["mustexist"] = False
        options["parent"] = self.lDeploymentFiles
        options["title"] = "Search:"
        self.tTestCommand.configure(state = "normal")
        self.tTestCommand.delete("1.0", "end")
        self.lTestCommandStr = tkinter.filedialog.askopenfilename()
        self.tTestCommand.insert("end", self.lTestCommandStr)
        self.tTestCommand.configure(state = "disabled")
        
    def searchForObb(self, event = None):
        self.dir_opt = options = {}
        options["initialdir"] = os.getcwd()
        options["mustexist"] = False
        options["parent"] = self.lDeploymentFiles
        options["title"] = "Search:"
        self.tObbFilePath.configure(state = "normal")
        self.tObbFilePath.delete("1.0", "end")
        self.lObbFilePathStr = tkinter.filedialog.askopenfilename()
        self.tObbFilePath.insert("end", self.lObbFilePathStr)
        self.tObbFilePath.configure(state = "disabled")
        
    def getTestCommands(self, test_path, application_id, apk_path, obb_path, app_name, launch_activity):
        test_commands = []
        if os.path.exists(test_path):
            self.test_info = None
            with open(test_path, 'rt') as tFile:
                self.test_info = tFile.read()
            if self.test_info is not None:
                test_commands = self.parse_test(application_id, apk_path, obb_path, app_name, launch_activity)
        return test_commands
          
    def parse_test(self, application_id, apk_path, obb_path, app_name, launch_activity):
        args = []
        args.append("")
        args.append(application_id)
        args.append(apk_path)
        args.append(obb_path)
        args.append(app_name)
        args.append(launch_activity)
        if self.test_info is not None:
            print("TestInfo: " + self.test_info)
            test_line = ""
            try:
                test_line = self.test_info.format(args=args)
            except:
                print("Unable to format args...")
            return test_line.split('\n')
        else:
            return []
            
            
    def runTests(self):
        apk_path = self.lApkFilePathStr
        obb_path = self.lObbFilePathStr
        # app_name = self.get_app_name(self.tApkFilePath)
        # application_id = self.get_application_id(self.tApkFilePath)
        # launch_activity = self.get_app_launch_activity(self.tApkFilePath)
        app_name = "AngryBirds"
        application_id = "com.rovio.baba"
        launch_activity = "com.rovio.baba/rovio.baba.facebook.AbbaUnityActivity"
        self.test_commands = []
        try:
            self.test_commands = self.getTestCommands(self.lTestCommandStr, application_id, apk_path, obb_path, app_name, launch_activity)
        except:
            print("Caught error while parsing test commands")
            
        self.android_automators = []
        selectedDevices = self.testingDevicesView.selection()
        
        for device_id in selectedDevices:
            print("Device_id: " + device_id + " type: " + repr(type(device_id)))
            automator = AndroidAutomator(device_id, self.adb, apk_path, obb_path, app_name, launch_activity, self.test_commands)
            print("Automator for device: " + repr(device_id))
            self.android_automators.append(automator)
        
        for automator in self.android_automators:
            print("Executing automator: " + repr(automator.device_id))
            automator.initialize_automator_operations()
            automator.run_steps()
        
    def print_selection(self): 
        selection = self.list.curselection() 
        print([self.list.get(i) for i in selection]) 
        
    def add_device_for_testing(self, event = None):
        device_name = str(self.cbDevices.get())
        if len(device_name) > 0:
            device_name = device_name.strip('\t')
            self.testingDevicesView.insert("", "end", device_name, text=device_name)
            
    def remove_device_from_testing(self, event = None):
        device_name = str(self.cbDevices.get())
        if len(device_name) > 0:
            device_name = device_name.strip('\t')
            self.testingDevicesView.delete(device_name)
        
    def refresh_devices(self, event = None):
        self.list_of_connected_devices = {}
        self.adbDevicesResult = self.adb.call("devices", self.adb.devices);
        self.deviceOSVersions = {}
        # self.adb.get_sd_free_space()
        
        if isinstance(self.adbDevicesResult, list):
            if len(self.adbDevicesResult) > 1:
                for x in range(len(self.adbDevicesResult)):
                    key = "Device" + str(x)
                    value = self.adbDevicesResult[x]
                    self.list_of_connected_devices[value] = x
            else:
                if len(self.adbDevicesResult) > 0:
                    self.list_of_connected_devices[self.adbDevicesResult[0]] = 1
                
        self.cbDevices.config(values = [""] + list(self.list_of_connected_devices.keys()))
        self.cbDevices.bind("<<ComboboxSelected>>", self.on_device_selected)
        
        commandParams = ["devices"]
        self.genyShell.process_args(commandParams)
        gennyDevicesResult = self.genyShell.devices_info
        
    def on_item_selected(self, event = None):
        item_selected = self.items.get()
        self.item_selected = item_selected
                
    def on_device_selected(self, event = None):
        device_name = str(self.cbDevices.get())
        if len(device_name) > 0:
            device_name = device_name.strip('\t')
            client_processor = self.adb
            device_active = True
            if device_name in self.genyShell.devices_info.keys():
                client_processor = self.genyShell
                device_state = self.genyShell.devices_info[device_name].device_geny_state
                if device_state == "Aborted" or device_state == "Off":
                    device_active = False
                    print("Device: " + device_name + " was inactive. Turning it on!")
                    client_processor.turn_on_device(device_name)
                else:
                    commandParams = ["connect_to_device", self.genyShell.devices_info[device_name].device_geny_ip, self.genyShell.devices_info[device_name].device_port]
                    client_processor.process_args(commandParams)
                    
                    commandParams = ["get_os_version", self.genyShell.devices_info[device_name].device_geny_ip, self.genyShell.devices_info[device_name].device_port]
                    client_processor.process_args(commandParams)
                    self.deviceOSVersions[device_name] = self.adb.result
             
            else:
                commandParams = ["get_os_version", device_name]
                client_processor.process_args(commandParams)
                self.deviceOSVersions[device_name] = self.adb.result
                
                commandParams = ["get_free_space_location", device_name]
                client_processor.process_args(commandParams)
                
                commandParams = ["get_device_model", device_name]
                client_processor.process_args(commandParams)
                
                commandParams = ["list_packages", device_name]
                client_processor.process_args(commandParams)
            
            # self.selected_application = tk.StringVar()
            # choices = self.adb.devices_info[self.adb.current_device_name].device_applications
            
            # # Filter only needed applications eaither com.zplay (Taponomicon exception) or com.madheadgames.
            # applications = choices
            
            # self.selected_application.set(applications[0])
            
            # commandParams = ["clear_log", device_name]
            # self.adb.process_args(commandParams)

            # self.applications = tkinter.ttk.Combobox(self.lfApplicationUtils, state = "readonly", textvariable = self.selected_application, width = 40)
            # self.applications.config(values = applications)
            # self.applications.bind("<<ComboboxSelected>>", self.on_application_selected)
            # self.applications.grid(column = 0, row = 0, columnspan = 2, sticky = "N")
            # self.applications.set("")
            
            # self.bBackupApp = ttk.Button(self.lfApplicationUtils, text = "Backup Application", command = self.backup_application, width = 20)
            # self.bBackupApp.grid(column = 0, row = 2, sticky = 'W', pady = 5)
            
            # self.bClearPurchases = ttk.Button(self.lfApplicationUtils, text = "Clear Purchase", command = self.clear_purchase, width = 20)
            # self.bClearPurchases.grid(column = 0, row = 3, sticky = 'W', pady = 5)
            
            # self.bClearData = ttk.Button(self.lfApplicationUtils, text = "Clear Data & Cache", command = self.clear_data, width = 20)
            # self.bClearData.grid(column = 1, row = 2, sticky = 'W', pady = 5)
            
            # self.bClearData = ttk.Button(self.lfApplicationUtils, text = "Run Application", command = self.run_application, width = 20)
            # self.bClearData.grid(column = 1, row = 3, sticky = 'W', pady = 5)
            
            # self.selected_device = device_name
            # if not device_name in self.device_tabs:
                # self.device_tabs[device_name] = DeviceLogTab(self, device_name)
                # device_log = self.device_tabs[device_name]
                # device_log.show_console()
            
            
    def show_testing_options(self, event=None):
        # self.adb = ADB()
        # self.toplevel = tkinter.Toplevel()
        # self.toplevel.geometry("500x270+120+120")
        # self.toplevel.grid_columnconfigure(0, weight = 1, minsize = 300)
        # self.toplevel.grid_rowconfigure(1, weight = 1, minsize = 200)
        # self.toplevel.title("DeployWindow")
       
        # self.lDeploymentFiles = tkinter.LabelFrame(self.toplevel, text = "Deploy Files", padx = 5, pady = 5)
        # self.lDeploymentFiles.grid(column = 0, rowspan = 2, sticky = "NSWE", padx = 5, pady = 5)
        # self.lApkFilePathStr = ""
        # self.lApkFilePath = tkinter.Label(self.lDeploymentFiles, text="APK File: ").grid(row = 1)
        # self.tApkFilePath = tkinter.Text(self.lDeploymentFiles, height = 1, width = 40)
        # self.tApkFilePath.tag_configure("center", justify="center")
        # self.tApkFilePath.tag_add("center", 1.0, "end")
        # self.tApkFilePath.insert("end", self.lApkFilePathStr)
        # self.tApkFilePath.configure(state = "disabled")
        # self.tApkFilePath.grid(column = 1, row = 1, sticky = "WN", pady = 5)
        
        # self.bApkFileSearch = tkinter.Button(self.lDeploymentFiles, text = "Search",	padx = 5, command = self.ask_for_apk_file_path)
        # self.bApkFileSearch.grid(column = 2, row = 1, columnspan = 2, sticky = "WN", pady = 5)
        
        # self.lObbFilePathStr = ""
        # self.lObbFilePath = tkinter.Label(self.lDeploymentFiles, text="Obb File: ").grid(row = 2)
        # self.tObbFilePath = tkinter.Text(self.lDeploymentFiles, height = 1, width = 40)
        # self.tObbFilePath.tag_configure("center", justify="center")
        # self.tObbFilePath.tag_add("center", 1.0, "end")
        # self.tObbFilePath.insert("end", self.lObbFilePathStr)
        # self.tObbFilePath.configure(state = "disabled")
        # self.tObbFilePath.grid(column = 1, row = 2, sticky = "WN", pady = 5)
        
        # self.bObbFileSearch = tkinter.Button(self.lDeploymentFiles, text = "Search",	padx = 5, command = self.ask_for_obb_file_path)
        # self.bObbFileSearch.grid(column = 2, row = 2, columnspan = 2, sticky = "WN", pady = 5)
        
        # self.bDeployToDevice = tkinter.Button(self.lDeploymentFiles, text = "Deploy Build",	padx = 5, command = self.mtd_btn_deploy_to_device)
        # self.bDeployToDevice.grid(column = 2, row = 4, sticky = "WN", pady = 5)
        
        
        # self.toplevel.focus_set()
        pass
            
    def on_application_selected(self, event = None):
        application_name = str(self.applications.get())
        self.selected_application.set(application_name)
            
    def broadcast_message(self, message):
        commandParams = ["broadcast", self.adb.current_device_name, self.selected_application.get(), message]
        self.adb.process_args(commandParams)
    
    def enableButtons(self):
        for button in self.buttons:
            button.config(state = "normal")

    def disableButtons(self, clickedButton):
        for button in self.buttons:
            if button != clickedButton:
                button.config(state = "disabled")
                
    
    #parent methods
    def show_error(self, msg):
        self.parent.show_error(msg)
    
if __name__ == "__main__" :
    tabSound = TabTest(None);