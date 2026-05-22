# FTESC UART Protocol Specification

## Frame Format

Every frame follows this structure:

```
[Header] [Length] [Command] [Payload...] [CRC16] [Footer]
```

| Field       | Size     | Description                                      |
|-------------|----------|--------------------------------------------------|
| Header      | 1 byte   | `0xAA` for short frames (payload < 256 bytes)    |
|             |          | `0xBB` for long frames (payload >= 256 bytes)    |
| Length      | 1-2 bytes| Short: payload length (1 byte)                   |
|             |          | Long: payload length big-endian (2 bytes)        |
| Command     | 1 byte   | Command ID (see below)                           |
| Payload     | N bytes  | Command-specific data                            |
| CRC16       | 2 bytes  | CRC-16 MODBUS big-endian over [Command+Payload]  |
| Footer      | 1 byte   | `0xDD`                                           |

## CRC-16 Calculation

Polynomial: CRC-16/MODBUS (x^16 + x^15 + x^2 + 1)
Algorithm: Table-driven with two 256-byte lookup tables.
Initial value: `0xFFFF`

```python
def crc16_ftesc(data: bytes) -> int:
    hi, lo = 0xFF, 0xFF
    for byte in data:
        idx = lo ^ byte
        lo = hi ^ CRC_HI_TABLE[idx]
        hi = CRC_LO_TABLE[idx]
    return (hi << 8) | lo
```

## Commands

| ID  | Name                          | Payload              | Response           |
|-----|-------------------------------|----------------------|--------------------|
| 0   | OBTAIN_DATA_ONCE              | —                    | RealtimeData (23B) |
| 2   | CONTROL_AND_OBTAIN_DATA_ONCE  | Duty(2B)             | RealtimeData (23B) |
| 3   | SET_DUTY                      | Duty f16(2B)         | ACK                |
| 4   | SET_CURRENT                   | Current f32(4B)      | ACK                |
| 5   | SET_CURRENT_GEAR              | Current f32(4B)      | ACK                |
| 6   | SET_BRAKE_CURRENT             | Brake f32(4B)        | ACK                |
| 16  | CAN_FORWARD                   | CAN msg (var)        | —                  |
| 17  | OBTAIN_FIRMWARE_VERSION       | —                    | FirmwareInfo (5B)  |
| 25  | KEEP_ALIVE                    | —                    | ACK                |
| 26  | SET_AUTO_OBTAIN_REALTIME_DATA | Rate u16(2B)         | ACK                |
| 29  | RESET_AND_REBOOT              | —                    | —                  |
| 30  | OBTAIN_ALL_IDS                | —                    | ID list            |
| 32  | SET_CURRENT_GEAR_OBTAIN       | Current f32(4B)      | RealtimeData (23B) |
| 35  | REBOOT_FTESC                  | —                    | — (reboots)        |
| 37  | SET_ID_CURRENT                | ID+Current(5B)       | ACK                |
| 38  | SET_POSITION                  | Position f32(4B)     | ACK                |
| 39  | SET_SPEED                     | Speed f32(4B)        | ACK                |
| 40  | READ_CONFIG                   | CtrlID(1B)+SecID(1B) | ConfigData (var)   |
| 41  | WRITE_CONFIG                  | CtrlID(1B)+SecID(1B)+Data | ACK           |
| 42  | READ_ALL_CONFIG               | CtrlID(1B)           | AllConfig (var)    |
| 43  | WRITE_ALL_CONFIG              | CtrlID(1B)+AllData   | ACK                |
| 60  | ENTER_BOOTLOADER              | —                    | — (reboots to bootloader) |
| 61  | CHECK_MCU_HEALTH              | —                    | Health byte (0=OK, 1=Corrupt, 2=Unknown) |

## Data Types

| Type | Size   | Encoding                          |
|------|--------|-----------------------------------|
| u8   | 1 byte | Raw byte                          |
| u16  | 2 bytes| Big-endian unsigned               |
| u24  | 3 bytes| Big-endian unsigned               |
| u32  | 4 bytes| Big-endian unsigned               |
| i16  | 2 bytes| Big-endian signed                 |
| i24  | 3 bytes| Big-endian signed (two's comp)    |
| i32  | 4 bytes| Big-endian signed                 |
| f16  | 2 bytes| `int(value × 100)` as i16         |
| f32  | 4 bytes| `int(value × 1e6)` as i32         |
| af32 | 4 bytes| IEEE-754-like via frexp           |

### af32 Encoding

```
value = frexp(real) → (mantissa, exponent)
mantissa_abs = abs(mantissa)
uint = int((mantissa_abs - 0.5) * 2.0 * 8388608.0)
exponent += 126
result = (exponent << 23) | (uint & 0x7FFFFF)
if mantissa < 0: result |= (1 << 31)
```

## Real-time Data Frame (23 bytes)

| Offset | Size | Field          | Type |
|--------|------|----------------|------|
| 0      | 1    | controller_id  | u8   |
| 1      | 1    | fault          | u8   |
| 2      | 2    | inp_voltage    | f16  |
| 4      | 4    | input_current  | f32  |
| 8      | 4    | motor_current  | f32  |
| 12     | 4    | rpm            | f32  |
| 16     | 2    | duty_cycle_now | f16  |
| 18     | 2    | temp_fet       | f16  |
| 20     | 2    | temp_motor     | f16  |
| 22     | 1    | cpu_load       | f16  |
| —      | —    | encoder_angle  | f32  (if available via long frame) |

## Firmware Info Frame (5 bytes)

| Offset | Size | Field          | Type |
|--------|------|----------------|------|
| 0      | 1    | controller_id  | u8   |
| 1      | 1    | version_major  | u8   |
| 2      | 1    | version_minor  | u8   |
| 3      | 1    | version_patch  | u8   |
| 4      | 1    | model_type     | u8   |

## Configuration Sections

12 sections, each encodable independently:

| ID | Name          | Controller | Fields | Description              |
|----|---------------|------------|--------|--------------------------|
| 0  | motor         | A/B        | 10     | Motor type, poles, KV... |
| 1  | hall          | A/B        | 7      | Hall sensors             |
| 2  | foc           | A/B        | 15     | FOC parameters           |
| 3  | limits        | A/B        | 15     | Current/voltage limits   |
| 4  | ramp          | A/B        | 6      | Acceleration ramps       |
| 5  | brake         | A/B        | 5      | Braking config           |
| 6  | input_control | Global     | 15     | Throttle/brake input     |
| 7  | speed_pid     | Global     | 6      | Speed PID gains          |
| 8  | battery       | Global     | 9      | Battery parameters       |
| 9  | dual_setup    | Global     | 13     | Dual motor sync          |
| 10 | imu           | Global     | 8      | IMU settings             |
| 11 | can           | Global     | 9      | CAN bus config           |

### Controller IDs

| ID  | Target         |
|-----|----------------|
| 0   | Motor A        |
| 1   | Motor B        |
| 127 | Global config  |

### Read Config Command (40)

Request:
```
[0xAA] [0x02] [0x28] [CtrlID] [SecID] [CRC16] [0xDD]
```

Response:
```
[0xAA] [N+2] [0x28] [CtrlID] [SecID] [FieldData...N bytes] [CRC16] [0xDD]
```

### Write Config Command (41)

Request:
```
[0xAA] [N+2] [0x29] [CtrlID] [SecID] [FieldData...N bytes] [CRC16] [0xDD]
```

Response: ACK (echo of command)

### Read All Config Command (42)

Reads all 12 sections for one controller in a single response.

### Write All Config Command (43)

Writes all 12 sections to one controller in a single frame.

## Config Field Serialization

Each section has a fixed set of fields in a specific order. See
`ftesc/config_protocol.py` for the complete field definitions.

Common field types used in config:
- `bool`: 1 byte (0/1)
- `u8`: 1 byte (enums, small ints)
- `u16`: 2 bytes (pole_pairs, cells, CAN IDs)
- `u32`: 4 bytes (rare)
- `f16(×100)`: 2 bytes (voltages, temperatures, percentages)
- `f16(×10000)`: 2 bytes (duty cycle, precision values)
- `f32(×1e6)`: 4 bytes (currents, RPM, gains)
- `f32(×1)`: 4 bytes (RPM, ERPM)
- `curve`: 6 × f32 = 24 bytes (throttle/brake curves)
- `hall_table`: 8 bytes (Hall sensor transition table)
