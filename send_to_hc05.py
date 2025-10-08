#!/usr/bin/env python3
"""
send_to_hc05.py

Simple script that reads IMU data (MPU6050 or simulated) and sends formatted
gyro and accelerometer values over a serial connection to an HC-05 module.

Features:
- Auto-detect HC-05 serial port (by scanning serial ports for 'HC-05', 'HC05', or 'Bluetooth')
- Connect at a configurable baud (default 9600) and send at 50 Hz
- Reconnect automatically on errors
- MPU6050 support via `mpu6050` package (optional) or a simulated IMU

Usage:
  python send_to_hc05.py --imu sim
  python send_to_hc05.py --imu mpu --baud 9600

Dependencies:
  pip install pyserial
  pip install mpu6050 (optional, only if using --imu mpu)
"""

import time
import argparse
import sys
import threading

try:
    import serial
    from serial.tools import list_ports
except Exception:
    print('pyserial is required. Install with: pip install pyserial')
    raise

import math


class IMUBase:
    def read(self):
        raise NotImplementedError()


class SimulatedIMU(IMUBase):
    def __init__(self):
        self.t0 = time.time()

    def read(self):
        t = time.time() - self.t0
        gx = math.sin(t * 2.0) * 30.0
        gy = math.sin(t * 1.5) * 20.0
        gz = math.sin(t * 0.7) * 10.0
        ax = math.sin(t * 0.9) * 1.2
        ay = math.cos(t * 0.8) * 0.6
        az = 9.81 + math.sin(t * 0.5) * 0.2
        return {'gx': gx, 'gy': gy, 'gz': gz, 'ax': ax, 'ay': ay, 'az': az}


class MPU6050IMU(IMUBase):
    def __init__(self, address=0x68):
        try:
            from mpu6050 import mpu6050
        except Exception as e:
            raise RuntimeError('mpu6050 package not installed or not importable: %s' % e)
        self.sensor = mpu6050(address)

    def read(self):
        accel = self.sensor.get_accel_data()
        gyro = self.sensor.get_gyro_data()
        # many mpu6050 libs return accel in g and gyro in deg/s
        ax = float(accel.get('x', 0.0))
        ay = float(accel.get('y', 0.0))
        az = float(accel.get('z', 0.0))
        gx = float(gyro.get('x', 0.0))
        gy = float(gyro.get('y', 0.0))
        gz = float(gyro.get('z', 0.0))
        return {'gx': gx, 'gy': gy, 'gz': gz, 'ax': ax, 'ay': ay, 'az': az}


def find_hc05_port(timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        ports = list_ports.comports()
        for p in ports:
            desc = (p.description or '').lower()
            hwid = (p.hwid or '').lower()
            if 'hc-05' in desc or 'hc-05' in hwid or 'hc05' in desc or 'hc05' in hwid or 'bluetooth' in desc or 'bluetooth' in hwid:
                return p.device
        time.sleep(0.5)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--imu', choices=['sim','mpu'], default='sim')
    parser.add_argument('--baud', type=int, default=9600, help='HC-05 serial baud')
    parser.add_argument('--port', help='Force serial port (skips auto-detect)')
    parser.add_argument('--rate', type=float, default=50.0, help='Send rate in Hz')
    args = parser.parse_args()

    if args.imu == 'mpu':
        try:
            imu = MPU6050IMU()
        except Exception as e:
            print('Failed to initialize MPU6050:', e)
            print('Falling back to simulated IMU.')
            imu = SimulatedIMU()
    else:
        imu = SimulatedIMU()

    interval = 1.0 / args.rate

    ser = None
    connected = False

    print('Starting IMU -> HC-05 sender. Target rate: %.1f Hz' % args.rate)
    try:
        while True:
            if not connected:
                port = args.port or find_hc05_port(timeout=3.0)
                if not port:
                    print('HC-05 not found. Waiting and retrying...')
                    time.sleep(1.0)
                    continue
                try:
                    print('Connecting to HC-05 on', port, 'at', args.baud)
                    ser = serial.Serial(port, args.baud, timeout=1)
                    connected = True
                    print('Connected to', port)
                except Exception as e:
                    print('Failed to open serial port', port, e)
                    time.sleep(1.0)
                    continue

            # read IMU
            try:
                sample = imu.read()
            except Exception as e:
                print('IMU read error:', e)
                sample = {'gx':0,'gy':0,'gz':0,'ax':0,'ay':0,'az':0}

            line = 'Gx:{gx:.3f} Gy:{gy:.3f} Gz:{gz:.3f} Ax:{ax:.3f} Ay:{ay:.3f} Az:{az:.3f}\n'.format(**sample)

            if connected and ser:
                try:
                    ser.write(line.encode('utf-8'))
                    ser.flush()
                except Exception as e:
                    print('Serial write error, will reconnect:', e)
                    try:
                        ser.close()
                    except Exception:
                        pass
                    ser = None
                    connected = False
                    time.sleep(0.5)
                    continue

            time.sleep(interval)

    except KeyboardInterrupt:
        print('\nStopping...')
    finally:
        try:
            if ser and ser.is_open:
                ser.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()
