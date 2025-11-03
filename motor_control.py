#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dynamixel 4-Motor Control with 2 COM Ports
- Controls 2 XL330-M288-T and 2 XL430-W250-T motors
- Uses 2 OpenRB-150 controllers (2 motors per controller)
- Key commands: 'w' for +90°, 's' for -90°, 'q' to quit
"""

import os
import time

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import *

#********* DYNAMIXEL Configuration *********
# Protocol 2.0 for XL330 and XL430
PROTOCOL_VERSION            = 2.0

# Control table addresses for X-Series (XL330, XL430)
ADDR_TORQUE_ENABLE          = 64
ADDR_GOAL_POSITION          = 116
ADDR_PRESENT_POSITION       = 132
ADDR_PROFILE_VELOCITY       = 112
ADDR_PROFILE_ACCELERATION   = 108
LEN_GOAL_POSITION           = 4

# Motor IDs
# Port 1 (COM port 1): XL330 motors
PORT1_MOTOR1_ID             = 1     # XL330-M288-T #1
PORT1_MOTOR2_ID             = 2     # XL330-M288-T #2

# Port 2 (COM port 2): XL430 motors
PORT2_MOTOR1_ID             = 1     # XL430-W250-T #1
PORT2_MOTOR2_ID             = 2     # XL430-W250-T #2

# COM Port settings (수정 필요: 실제 COM 포트 번호로 변경)
DEVICENAME_PORT1            = 'COM3'    # XL330 연결된 포트
DEVICENAME_PORT2            = 'COM4'    # XL430 연결된 포트

# Position settings
BAUDRATE                    = 57600
TORQUE_ENABLE               = 1
TORQUE_DISABLE              = 0
DXL_MOVING_STATUS_THRESHOLD = 20

# Angle to position conversion (0~4095 = 0~360 degrees)
# Center: 2048 = 180 degrees
POSITION_CENTER             = 2048
POSITION_MINUS_90           = 1024      # 90 degrees (180 - 90)
POSITION_PLUS_90            = 3072      # 270 degrees (180 + 90)

# Profile settings for smooth 5-second motion
# Profile Velocity: 설정값이 작을수록 느리게 움직임
# 5초 동안 90도(1024 position units) 이동
# Velocity unit: 0.229 rpm per unit
# 대략 50-100 정도면 5초에 걸쳐 부드럽게 이동
PROFILE_VELOCITY_VALUE      = 50
PROFILE_ACCELERATION_VALUE  = 20


def initialize_port(device_name, baudrate):
    """COM 포트 초기화"""
    port_handler = PortHandler(device_name)
    packet_handler = PacketHandler(PROTOCOL_VERSION)

    if not port_handler.openPort():
        print(f"Failed to open port {device_name}")
        return None, None
    print(f"Succeeded to open port {device_name}")

    if not port_handler.setBaudRate(baudrate):
        print(f"Failed to set baudrate on {device_name}")
        return None, None
    print(f"Succeeded to set baudrate to {baudrate}")

    return port_handler, packet_handler


def enable_torque(port_handler, packet_handler, motor_id):
    """모터 토크 활성화"""
    dxl_comm_result, dxl_error = packet_handler.write1ByteTxRx(
        port_handler, motor_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE
    )
    if dxl_comm_result != COMM_SUCCESS:
        print(f"[ID:{motor_id}] {packet_handler.getTxRxResult(dxl_comm_result)}")
        return False
    elif dxl_error != 0:
        print(f"[ID:{motor_id}] {packet_handler.getRxPacketError(dxl_error)}")
        return False
    print(f"Motor ID {motor_id} torque enabled")
    return True


def disable_torque(port_handler, packet_handler, motor_id):
    """모터 토크 비활성화"""
    dxl_comm_result, dxl_error = packet_handler.write1ByteTxRx(
        port_handler, motor_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE
    )
    if dxl_comm_result != COMM_SUCCESS:
        print(f"[ID:{motor_id}] {packet_handler.getTxRxResult(dxl_comm_result)}")
    elif dxl_error != 0:
        print(f"[ID:{motor_id}] {packet_handler.getRxPacketError(dxl_error)}")


def set_profile_velocity(port_handler, packet_handler, motor_id, velocity):
    """Profile Velocity 설정 (움직임 속도)"""
    dxl_comm_result, dxl_error = packet_handler.write4ByteTxRx(
        port_handler, motor_id, ADDR_PROFILE_VELOCITY, velocity
    )
    if dxl_comm_result != COMM_SUCCESS:
        print(f"[ID:{motor_id}] Velocity set failed")
        return False
    return True


def set_profile_acceleration(port_handler, packet_handler, motor_id, acceleration):
    """Profile Acceleration 설정 (가속도)"""
    dxl_comm_result, dxl_error = packet_handler.write4ByteTxRx(
        port_handler, motor_id, ADDR_PROFILE_ACCELERATION, acceleration
    )
    if dxl_comm_result != COMM_SUCCESS:
        print(f"[ID:{motor_id}] Acceleration set failed")
        return False
    return True


def set_goal_position(group_sync_write, motor_id, goal_position):
    """목표 위치를 Sync Write에 추가"""
    # 4-byte position value를 byte array로 변환
    param_goal_position = [
        DXL_LOBYTE(DXL_LOWORD(goal_position)),
        DXL_HIBYTE(DXL_LOWORD(goal_position)),
        DXL_LOBYTE(DXL_HIWORD(goal_position)),
        DXL_HIBYTE(DXL_HIWORD(goal_position))
    ]

    dxl_addparam_result = group_sync_write.addParam(motor_id, param_goal_position)
    if not dxl_addparam_result:
        print(f"[ID:{motor_id}] groupSyncWrite addparam failed")
        return False
    return True


def move_motors_to_position(port1_handler, packet1_handler, port2_handler, packet2_handler,
                            sync_write1, sync_write2, position, description):
    """4개 모터를 동시에 목표 위치로 이동"""
    print(f"\n{description} (Position: {position})")

    # Port 1: XL330 motors
    if not set_goal_position(sync_write1, PORT1_MOTOR1_ID, position):
        return False
    if not set_goal_position(sync_write1, PORT1_MOTOR2_ID, position):
        return False

    # Port 2: XL430 motors
    if not set_goal_position(sync_write2, PORT2_MOTOR1_ID, position):
        return False
    if not set_goal_position(sync_write2, PORT2_MOTOR2_ID, position):
        return False

    # Send sync write commands
    dxl_comm_result = sync_write1.txPacket()
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Port 1 sync write failed: {packet1_handler.getTxRxResult(dxl_comm_result)}")

    dxl_comm_result = sync_write2.txPacket()
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Port 2 sync write failed: {packet2_handler.getTxRxResult(dxl_comm_result)}")

    # Clear parameter storage
    sync_write1.clearParam()
    sync_write2.clearParam()

    print(f"Motors moving to {description}... (약 5초 소요)")
    return True


def main():
    print("=" * 60)
    print("  Dynamixel 4-Motor Control System")
    print("=" * 60)
    print("Controls:")
    print("  'w' - Move all motors to +90 degrees")
    print("  's' - Move all motors to -90 degrees")
    print("  'q' - Quit program")
    print("=" * 60)

    # Initialize Port 1 (XL330 motors)
    port1_handler, packet1_handler = initialize_port(DEVICENAME_PORT1, BAUDRATE)
    if port1_handler is None:
        return

    # Initialize Port 2 (XL430 motors)
    port2_handler, packet2_handler = initialize_port(DEVICENAME_PORT2, BAUDRATE)
    if port2_handler is None:
        port1_handler.closePort()
        return

    # Initialize GroupSyncWrite for both ports
    sync_write_port1 = GroupSyncWrite(port1_handler, packet1_handler,
                                      ADDR_GOAL_POSITION, LEN_GOAL_POSITION)
    sync_write_port2 = GroupSyncWrite(port2_handler, packet2_handler,
                                      ADDR_GOAL_POSITION, LEN_GOAL_POSITION)

    # Enable torque for all motors
    print("\nEnabling torque for all motors...")
    motors_ok = True
    motors_ok &= enable_torque(port1_handler, packet1_handler, PORT1_MOTOR1_ID)
    motors_ok &= enable_torque(port1_handler, packet1_handler, PORT1_MOTOR2_ID)
    motors_ok &= enable_torque(port2_handler, packet2_handler, PORT2_MOTOR1_ID)
    motors_ok &= enable_torque(port2_handler, packet2_handler, PORT2_MOTOR2_ID)

    if not motors_ok:
        print("Failed to enable torque on one or more motors")
        port1_handler.closePort()
        port2_handler.closePort()
        return

    # Set profile velocity and acceleration for smooth motion
    print("\nSetting motion profiles for 5-second movement...")
    set_profile_velocity(port1_handler, packet1_handler, PORT1_MOTOR1_ID, PROFILE_VELOCITY_VALUE)
    set_profile_velocity(port1_handler, packet1_handler, PORT1_MOTOR2_ID, PROFILE_VELOCITY_VALUE)
    set_profile_velocity(port2_handler, packet2_handler, PORT2_MOTOR1_ID, PROFILE_VELOCITY_VALUE)
    set_profile_velocity(port2_handler, packet2_handler, PORT2_MOTOR2_ID, PROFILE_VELOCITY_VALUE)

    set_profile_acceleration(port1_handler, packet1_handler, PORT1_MOTOR1_ID, PROFILE_ACCELERATION_VALUE)
    set_profile_acceleration(port1_handler, packet1_handler, PORT1_MOTOR2_ID, PROFILE_ACCELERATION_VALUE)
    set_profile_acceleration(port2_handler, packet2_handler, PORT2_MOTOR1_ID, PROFILE_ACCELERATION_VALUE)
    set_profile_acceleration(port2_handler, packet2_handler, PORT2_MOTOR2_ID, PROFILE_ACCELERATION_VALUE)

    # Initialize all motors to -90 degrees
    print("\n" + "=" * 60)
    print("Initializing all motors to -90 degrees...")
    print("=" * 60)
    move_motors_to_position(port1_handler, packet1_handler, port2_handler, packet2_handler,
                           sync_write_port1, sync_write_port2, POSITION_MINUS_90,
                           "Initial position: -90°")
    time.sleep(6)  # Wait for motors to reach position

    print("\n" + "=" * 60)
    print("Ready! Press 'w' for +90°, 's' for -90°, 'q' to quit")
    print("=" * 60)

    # Main control loop
    try:
        while True:
            key = getch()

            if key == 'w' or key == 'W':
                move_motors_to_position(port1_handler, packet1_handler, port2_handler, packet2_handler,
                                       sync_write_port1, sync_write_port2, POSITION_PLUS_90,
                                       "Moving to +90°")
                time.sleep(6)  # Wait for motion to complete
                print("✓ Reached +90°")

            elif key == 's' or key == 'S':
                move_motors_to_position(port1_handler, packet1_handler, port2_handler, packet2_handler,
                                       sync_write_port1, sync_write_port2, POSITION_MINUS_90,
                                       "Moving to -90°")
                time.sleep(6)  # Wait for motion to complete
                print("✓ Reached -90°")

            elif key == 'q' or key == 'Q':
                print("\nQuitting...")
                break

            else:
                print(f"Unknown key: '{key}'. Use 'w', 's', or 'q'")

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    finally:
        # Disable torque for all motors
        print("\nDisabling torque...")
        disable_torque(port1_handler, packet1_handler, PORT1_MOTOR1_ID)
        disable_torque(port1_handler, packet1_handler, PORT1_MOTOR2_ID)
        disable_torque(port2_handler, packet2_handler, PORT2_MOTOR1_ID)
        disable_torque(port2_handler, packet2_handler, PORT2_MOTOR2_ID)

        # Close ports
        port1_handler.closePort()
        port2_handler.closePort()
        print("Ports closed. Goodbye!")


if __name__ == "__main__":
    main()
