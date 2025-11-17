from machine import Pin
import machine
import utime
import select
import sys
import time

# Pin Setup
DIR_PIN = Pin(26, Pin.OUT)
STEP_PIN = Pin(27, Pin.OUT)
EN_PIN = Pin(28, Pin.OUT)
EN_PIN.value(0)  # Enable stepper motor

Light_R_Pin = Pin(0, Pin.IN, Pin.PULL_UP)  # Right sensor
Light_L_Pin = Pin(2, Pin.IN, Pin.PULL_UP)  # Left sensor

# Pneumatic actuator (two-pin control)
PNEUMATIC_IN1 = machine.Pin(16, machine.Pin.OUT)  # actuator control
PNEUMATIC_IN2 = machine.Pin(17, machine.Pin.OUT)  # enable/supply line
PNEUMATIC_IN2.value(1)  # keep enable line HIGH

def pneumatic_up():
    PNEUMATIC_IN1.value(1)  # set actuator for pneumatic up

def pneumatic_down():
    PNEUMATIC_IN1.value(0)  # set actuator for pneumatic down
    
# Stepper move function
def stepper_move(duration, direction, delay=500):
    DIR_PIN.value(direction)
    start_time = utime.ticks_ms()
    
    while utime.ticks_diff(utime.ticks_ms(), start_time) < duration:
        STEP_PIN.value(1)
        utime.sleep_us(delay)
        STEP_PIN.value(0)
        utime.sleep_us(delay)

# Check serial input (from detection code)
def check_serial(): 
    rlist, _, _ = select.select([sys.stdin], [], [], 0)
    if rlist:
        line = sys.stdin.readline().strip()
        print("Received:", line)
        if line == "DEFECT": # If defect received, actuate pneumatic
            stepper_move(1700, 0)
            pneumatic_up()
            time.sleep(2)
            pneumatic_down()

try:
    print("Starting stepper motor... Press Ctrl+C to stop")
    pneumatic_down()
    while True:
        check_serial()
        stepper_move(100, 0)  # Move a little initially

        if not Light_R_Pin.value():  # Sensor triggered (active low)
            start_time = utime.ticks_ms()  # Start time tracking

            while Light_L_Pin.value():  # Wait until Light_L is triggered
                stepper_move(1, 0)  # Move backward step-by-step
            
            duration = utime.ticks_diff(utime.ticks_ms(), start_time)
            stepper_move(duration // 2, 1)  # Move forward half the time

except KeyboardInterrupt:
    print("\nStopping stepper motor...")
    EN_PIN.value(1)  # Disable stepper motor
    print("Stepper motor stopped.")
