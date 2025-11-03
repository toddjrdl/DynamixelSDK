#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dynamixel Motor ID Scanner
- 각 COM 포트에 연결된 모터의 ID를 스캔합니다
"""

from dynamixel_sdk import *
import time

# Protocol 2.0
PROTOCOL_VERSION = 2.0
BAUDRATE = 57600

# COM 포트 설정 (실제 포트 번호로 수정)
PORTS = ['COM11', 'COM8']  # 실제 사용 중인 포트

# Control table address
ADDR_ID = 7
ADDR_MODEL_NUMBER = 0

def scan_port(port_name):
    """특정 포트에서 ID 1-10까지 스캔"""
    print(f"\n{'='*60}")
    print(f"Scanning {port_name}...")
    print(f"{'='*60}")

    port_handler = PortHandler(port_name)
    packet_handler = PacketHandler(PROTOCOL_VERSION)

    if not port_handler.openPort():
        print(f"Failed to open {port_name}")
        return []

    if not port_handler.setBaudRate(BAUDRATE):
        print(f"Failed to set baudrate on {port_name}")
        port_handler.closePort()
        return []

    found_motors = []

    # ID 1부터 10까지 스캔
    for dxl_id in range(1, 11):
        # Ping으로 모터 확인
        dxl_model_number, dxl_comm_result, dxl_error = packet_handler.ping(port_handler, dxl_id)

        if dxl_comm_result == COMM_SUCCESS:
            print(f"  [ID:{dxl_id:03d}] Found! Model Number: {dxl_model_number}")

            # 모델 번호로 모터 종류 확인
            model_name = "Unknown"
            if dxl_model_number == 1190:
                model_name = "XL330-M288-T"
            elif dxl_model_number == 1060:
                model_name = "XL430-W250-T"
            elif dxl_model_number == 1020:
                model_name = "XL320"
            elif dxl_model_number == 1120:
                model_name = "XL330-M077-T"

            print(f"           Motor Type: {model_name}")
            found_motors.append({
                'id': dxl_id,
                'model': dxl_model_number,
                'name': model_name
            })

    if not found_motors:
        print(f"  No motors found on {port_name}")

    port_handler.closePort()
    return found_motors

def main():
    print("="*60)
    print("  Dynamixel Motor ID Scanner")
    print("="*60)
    print("This tool scans COM ports to find connected Dynamixel motors")
    print("Scanning IDs from 1 to 10...")

    all_results = {}

    for port in PORTS:
        motors = scan_port(port)
        all_results[port] = motors
        time.sleep(0.5)

    # 요약 출력
    print("\n" + "="*60)
    print("  SCAN RESULTS SUMMARY")
    print("="*60)

    for port, motors in all_results.items():
        print(f"\n{port}:")
        if motors:
            for motor in motors:
                print(f"  - ID {motor['id']}: {motor['name']} (Model: {motor['model']})")
        else:
            print("  - No motors found")

    print("\n" + "="*60)
    print("  RECOMMENDED CONFIGURATION")
    print("="*60)

    # Port 1 설정
    if PORTS[0] in all_results and all_results[PORTS[0]]:
        print(f"\nPort 1 ({PORTS[0]}):")
        port1_motors = all_results[PORTS[0]]
        if len(port1_motors) >= 1:
            print(f"  PORT1_MOTOR1_ID = {port1_motors[0]['id']}  # {port1_motors[0]['name']}")
        if len(port1_motors) >= 2:
            print(f"  PORT1_MOTOR2_ID = {port1_motors[1]['id']}  # {port1_motors[1]['name']}")

    # Port 2 설정
    if PORTS[1] in all_results and all_results[PORTS[1]]:
        print(f"\nPort 2 ({PORTS[1]}):")
        port2_motors = all_results[PORTS[1]]
        if len(port2_motors) >= 1:
            print(f"  PORT2_MOTOR1_ID = {port2_motors[0]['id']}  # {port2_motors[0]['name']}")
        if len(port2_motors) >= 2:
            print(f"  PORT2_MOTOR2_ID = {port2_motors[1]['id']}  # {port2_motors[1]['name']}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
