# Dynamixel 4-Motor Control System

## 개요
이 프로그램은 2개의 OpenRB-150을 사용하여 4개의 Dynamixel 모터를 제어합니다.

### 하드웨어 구성
- **Port 1 (COM3)**: XL330-M288-T 2개 (ID: 1, 2)
- **Port 2 (COM4)**: XL430-W250-T 2개 (ID: 1, 2)

## 사전 요구사항

### 1. Python 설치
- Python 3.6 이상 필요

### 2. Dynamixel SDK 설치
```bash
pip install dynamixel-sdk
```

또는 이 리포지토리에서 직접 설치:
```bash
cd python
pip install .
```

### 3. COM 포트 확인
Windows에서 COM 포트 번호 확인:
1. 장치 관리자 열기
2. "포트(COM & LPT)" 섹션 확인
3. OpenRB-150이 연결된 COM 포트 번호 확인

### 4. 모터 ID 설정
- 각 OpenRB-150에 연결된 모터의 ID를 1, 2로 설정해야 합니다.
- Dynamixel Wizard를 사용하여 모터 ID를 설정할 수 있습니다.

## 설정

### COM 포트 번호 수정
`motor_control.py` 파일의 44-45번째 줄을 실제 COM 포트 번호로 수정:

```python
DEVICENAME_PORT1            = 'COM3'    # XL330 연결된 포트 (실제 번호로 수정)
DEVICENAME_PORT2            = 'COM4'    # XL430 연결된 포트 (실제 번호로 수정)
```

### 모터 ID 확인
기본 설정:
- Port 1: Motor ID 1, 2 (XL330)
- Port 2: Motor ID 1, 2 (XL430)

다른 ID를 사용하는 경우 36-43번째 줄 수정:
```python
PORT1_MOTOR1_ID             = 1
PORT1_MOTOR2_ID             = 2
PORT2_MOTOR1_ID             = 1
PORT2_MOTOR2_ID             = 2
```

## 실행 방법

### Visual Studio Code Terminal에서 실행

1. VS Code에서 프로젝트 폴더 열기
2. 터미널 열기 (Ctrl + `)
3. 프로그램 실행:

```bash
python motor_control.py
```

### 또는 명령 프롬프트에서 실행

```bash
cd C:\path\to\DynamixelSDK
python motor_control.py
```

## 사용 방법

프로그램을 실행하면:

1. **초기화**: 모든 모터가 -90도 위치로 이동합니다 (약 5초 소요)

2. **키 명령어**:
   - `w` 또는 `W`: 모든 모터를 +90도로 이동 (5초에 걸쳐 부드럽게)
   - `s` 또는 `S`: 모든 모터를 -90도로 이동 (5초에 걸쳐 부드럽게)
   - `q` 또는 `Q`: 프로그램 종료

## 출력 예시

```
============================================================
  Dynamixel 4-Motor Control System
============================================================
Controls:
  'w' - Move all motors to +90 degrees
  's' - Move all motors to -90 degrees
  'q' - Quit program
============================================================
Succeeded to open port COM3
Succeeded to set baudrate to 57600
Succeeded to open port COM4
Succeeded to set baudrate to 57600

Enabling torque for all motors...
Motor ID 1 torque enabled
Motor ID 2 torque enabled
Motor ID 1 torque enabled
Motor ID 2 torque enabled

Setting motion profiles for 5-second movement...

============================================================
Initializing all motors to -90 degrees...
============================================================

Initial position: -90° (Position: 1024)
Motors moving to Initial position: -90°... (약 5초 소요)

============================================================
Ready! Press 'w' for +90°, 's' for -90°, 'q' to quit
============================================================
```

## 문제 해결

### 1. "Failed to open port" 오류
- COM 포트 번호가 올바른지 확인
- 다른 프로그램이 포트를 사용 중인지 확인
- OpenRB-150이 컴퓨터에 제대로 연결되었는지 확인

### 2. "Failed to enable torque" 오류
- 모터 ID가 올바른지 확인
- 전원이 모터에 공급되고 있는지 확인
- Baudrate가 모터 설정과 일치하는지 확인 (기본값: 57600)

### 3. 모터가 움직이지 않음
- Torque Enable이 성공적으로 실행되었는지 확인
- 모터의 전원 공급 상태 확인
- Profile Velocity 값 조정 (더 빠른 움직임을 원하면 값을 높이기)

### 4. 움직임 속도 조정
`motor_control.py`의 60-61번째 줄에서 속도 조정:

```python
PROFILE_VELOCITY_VALUE      = 50    # 값을 높이면 빠르게 이동
PROFILE_ACCELERATION_VALUE  = 20    # 값을 높이면 빠르게 가속
```

- 5초보다 빠르게 움직이려면: 값을 증가 (예: 100)
- 5초보다 느리게 움직이려면: 값을 감소 (예: 30)

## 기술 세부사항

### 각도와 Position 값 변환
- Dynamixel XL330/XL430: 0~4095 = 0~360도
- 중앙(180도): Position 2048
- -90도(90도): Position 1024
- +90도(270도): Position 3072

### Control Table 주소 (Protocol 2.0)
- Torque Enable: 64
- Goal Position: 116
- Present Position: 132
- Profile Velocity: 112
- Profile Acceleration: 108

## 참고 자료
- [Dynamixel SDK Documentation](https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/)
- [XL330-M288-T Manual](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/)
- [XL430-W250-T Manual](https://emanual.robotis.com/docs/en/dxl/x/xl430-w250/)
