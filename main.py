import ue9
import threading
import LabJackPython
from pyModbusTCP.client import ModbusClient


class LabJack(ue9.UE9):
    def __init__(self, ip_address):
        super(LabJack, self).__init__()
        self.ethernet=True
        self.ip_address = ip_address
        self.getCalibrationData()
        self.streamConfig(NumChannels=4, 
                          ChannelNumbers=[0, 1, 2, 3], 
                          ChannelOptions=[8, 8, 8, 8], 
                          SettlingTime=0, 
                          Resolution=12, 
                          ScanFrequency=100)
        

class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

    def stopped(self) -> bool:
        return self.stop_event.is_set()
    

class LabJackReaderTask(StoppableThread):

    def __init__(self,
                 ip_address: str = "172.27.12.71"):
        
        super().__init__()

        self.ip_address = ip_address
        self.surge_val = 0.0
        self.sway_val = 0.0
        self.yaw_val = 0.0
        self.heavy_val = 0.0

    def init_lab_jack(self):
        try:
            self.lj = ue9.UE9(ethernet=True, ipAddress=self.ip_address)
            self.lj.getCalibrationData()
            self.lj.streamConfig(NumChannels=4, 
                                 ChannelNumbers=[0, 1, 2, 3], 
                                 ChannelOptions=[8, 8, 8, 8], 
                                 SettlingTime=0, 
                                 Resolution=12, 
                                 ScanFrequency=100)
            return 1
        except LabJackPython.LabJackException as e:
            print('Ошибка инициализации объекта')
            print(e)
            return -1
        
    
    def run(self):
        self.get_value()


    def get_value(self):
        try:
            self.lj.streamStart()

            for r in self.lj.streamData():
                if super().stopped():
                    print('\nLabJack thread was cancelled')
                    raise 
                
                self.surge_val = sum(r["AIN0"])/len(r["AIN0"]) 
                self.sway_val = sum(r["AIN1"])/len(r["AIN1"])
                self.yaw_val = sum(r["AIN2"])/len(r["AIN2"])
                self.heavy_val = sum(r["AIN3"])/len(r["AIN3"])              
        
        except:
            pass
            

    def reset_values(self):
        self.surge_val = 0.0
        self.sway_val = 0.0
        self.yaw_val = 0.0
        self.heavy_val = 0.0

    def values(self):
        return (self.surge_val, self.sway_val, self.yaw_val, self.heavy_val)



class ModbusServerWritter(StoppableThread):
    def __init__(self,
                 ip_address: str = "172.27.12.200",):
        
        super().__init__()

        self.ip_address = ip_address
        self.s = ModbusClient(host=self.ip_address, 
                              auto_open=False, 
                              auto_close=False)
        
    def run(self):
        self.write_value()

    def write_value(self):
        global lab_task
        self.s.open()
        try:
            while True:

                if super().stopped():
                    print('\nModbus thread was cancelled')
                    self.s.close()
                    return -1
                
                regs = [int((x+5)*1000) for x in lab_task.values()]

                try:
                    self.s.write_multiple_registers(regs_addr=0, regs_value=regs)
                except Exception as e:
                    print(e)
                
        except Exception as e:
            self.s.close()
            

if __name__ == "__main__":
    print('started main')


    lab_task = LabJackReaderTask()
    lab_task.init_lab_jack()
    lab_task.start()

    modbus_task = ModbusServerWritter()
    modbus_task.start()

    a = ''
    while a == '':
        a = input("any key for stop: ")
        lab_task.stop()
        modbus_task.stop()

