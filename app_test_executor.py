import socket
import sys
import os
import json
import traceback

from time import sleep

class AndroidAutomator(object):
    def __init__(self, device_id, adb, apk, obb, app_name, launch_activity, test_commands):
        self.adb = adb
        self.device_id = device_id
        self.apk_path = apk
        self.obb_path = obb
        self.apk_name = "com.rovio.baba_2020-07-15.apk"
        self.test_commands = test_commands
        self.operation_execution_count = 0
        self.operations = []
        self.running = False
        self.proceed = True
        self.app_name = app_name
        self.stopped_reason = ""
        self.launch_activity = launch_activity
    
    def initialize_automator_operations(self):
        for command in self.test_commands:
            print("Command: " + repr(command))
            if len(command) > 1: # if command is not empty
                command_parts = command.split(' ')
                print("Commands: " + repr(command_parts))
                self.operations.append(command_parts[0])
          
    def run_steps(self):
        function_to_call = None
        try:
            operations_index = 0
            self.running = True
            while self.proceed and (operations_index < len(self.operations)):
                print("operation " + str(operations_index + 1) + "/" + str(len(self.operations)), file=sys.stdout)
                function_to_call = self.operations[operations_index]
                getattr(self, '{}'.format(function_to_call))()
                self.operation_execution_count = operations_index
                operations_index += 1
                
                if operations_index >= len(self.operations):
                    self.build_completed = True
                
            if not self.proceed:
                print("There was error executing some of the operations", file=sys.stdout)
                            
        except Exception as error:
            traceback.print_exc()
            print("An exception was thrown! " + traceback.print_exc(), file=sys.stdout)
            self.operation_execution_count = 0
            
        print("Finished running all operations... Going back to idle")
        
    def remove_app(self):
        pass
        
    def run_app(self):
        device_name = self.device_id
        commandParams = ["start_app", device_name, self.launch_activity]
        self.adb.process_args(commandParams)
            
        self.operation_execution_count = self.operation_execution_count + 1
        
    def app_installed(self):
        commands_to_process = []
        shell_msg = "pm list packages | grep %s" % self.app_name
        commandParams = ["shell", self.device_id, shell_msg]
        print("Executing command: " + repr(commandParams))
        self.adb.process_args(commandParams)
        status = self.adb.result
        default_increase_counter = 2
        if status is None:
            default_increase_counter = 1
                
        self.operation_execution_count = self.operation_execution_count + default_increase_counter
        
    def install_apk(self):
        commands_to_process = []
        device_name = self.device_id
        commandParams = ["remove_dir", device_name, "/data/local/tmp/" + self.app_name]
        commands_to_process += [commandParams]
        commandParams = ["makeDir", device_name, "/data/local/tmp/" + self.app_name]
        commands_to_process += [commandParams]
        commandParams = ["upload", device_name, self.apk_path, "/data/local/tmp/" + self.app_name]
        commands_to_process += [commandParams]
        commandParams = ["reinstall", device_name, "/data/local/tmp/" + self.app_name + "/" + self.apk_name]
        commands_to_process += [commandParams]
            
        for command in commands_to_process:
            print("Executing command: " + repr(command))
            self.adb.process_args(command)
            
        self.operation_execution_count = self.operation_execution_count + 1

if __name__ == '__main__':
	DEVICE_CONNECTOR = AndroidAutomator()
	DEVICE_CONNECTOR.initialize_automator_operations()