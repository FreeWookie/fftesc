# -*- coding: utf-8 -*-
"""
tests/test_transport_recovery.py — Tests for recovery features in ftesc/transport.py
"""
import sys
import unittest
from unittest.mock import MagicMock, patch, call
import time
import queue

# Ensure the project root is in the path
sys.path.insert(0, '.')

from ftesc.transport import FtescTransport, ConnectionState
from ftesc.protocol import UartCommand
from ftesc.protocol import build_frame


class TestTransportRecovery(unittest.TestCase):
    def setUp(self):
        self.transport = FtescTransport()
        # Mock the serial connection
        self.transport._serial = MagicMock()
        self.transport._serial.is_open = True
        self.transport._state = ConnectionState.CONNECTED
        # Clear queues
        self.transport._response_queue = queue.Queue()
        self.transport._data_queue = queue.Queue()
        self.transport._event_queue = queue.Queue()

    def test_enter_bootloader(self):
        """Test that enter_bootloader sends the correct frame and disconnects after delay."""
        # Keep a reference to the mock serial because disconnect will set _serial to None
        mock_serial = self.transport._serial
        # Mock time.sleep to avoid waiting
        with patch('time.sleep') as mock_sleep:
            self.transport.enter_bootloader()
            # Check that send was called with a frame built from ENTER_BOOTLOADER and empty payload
            expected_frame = build_frame(UartCommand.ENTER_BOOTLOADER, b'')
            mock_serial.write.assert_called_once_with(expected_frame)
            # Check that sleep was called with approximately 2 seconds
            mock_sleep.assert_called_once()
            # The argument to sleep should be close to 2.0
            args, _ = mock_sleep.call_args
            self.assertAlmostEqual(args[0], 2.0, places=1)
            # Check that disconnect was called: state should be DISCONNECTED and _serial should be None
            self.assertEqual(self.transport._state, ConnectionState.DISCONNECTED)
            self.assertIsNone(self.transport._serial)

    def test_check_mcu_health_success(self):
        """Test check_mcu_health returns correct status for healthy MCU."""
        # Simulate a response in the response queue: (command, payload)
        # We'll put a response with command CHECK_MCU_HEALTH and payload b'\x00' (healthy)
        self.transport._response_queue.put((UartCommand.CHECK_MCU_HEALTH, b'\x00'))
        result = self.transport.check_mcu_health()
        self.assertEqual(result, "Sain")
        # Ensure the response was consumed
        self.assertTrue(self.transport._response_queue.empty())

    def test_check_mcu_health_corrupt(self):
        """Test check_mcu_health returns 'Corrompu' for corrupt MCU."""
        self.transport._response_queue.put((UartCommand.CHECK_MCU_HEALTH, b'\x01'))
        result = self.transport.check_mcu_health()
        self.assertEqual(result, "Corrompu")

    def test_check_mcu_health_unknown(self):
        """Test check_mcu_health returns 'Inconnu' for unknown health byte."""
        self.transport._response_queue.put((UartCommand.CHECK_MCU_HEALTH, b'\x02'))
        result = self.transport.check_mcu_health()
        self.assertEqual(result, "Inconnu")

    def test_check_mcu_health_error_byte(self):
        """Test check_mcu_health returns error string for unknown health byte."""
        self.transport._response_queue.put((UartCommand.CHECK_MCU_HEALTH, b'\x03'))
        result = self.transport.check_mcu_health()
        self.assertEqual(result, "Erreur (octet inconnu: 3)")

    def test_check_mcu_health_wrong_command_first(self):
        """Test that wrong command responses are ignored until correct command arrives."""
        # First put a wrong command response
        self.transport._response_queue.put((UartCommand.OBTAIN_DATA_ONCE, b''))
        # Then put the correct one
        self.transport._response_queue.put((UartCommand.CHECK_MCU_HEALTH, b'\x00'))
        result = self.transport.check_mcu_health()
        self.assertEqual(result, "Sain")
        # The wrong command should still be in the queue? Actually, we consume until we get the right one.
        # After the call, the wrong command should have been consumed as well because we keep calling get.
        # Let's check: we called get twice, so both items are gone.
        self.assertTrue(self.transport._response_queue.empty())

    def test_check_mcu_health_empty_payload(self):
        """Test that empty payload is ignored and we continue waiting."""
        # First put an empty payload (length 0) for the correct command - should be ignored
        self.transport._response_queue.put((UartCommand.CHECK_MCU_HEALTH, b''))
        # Then put a valid one
        self.transport._response_queue.put((UartCommand.CHECK_MCU_HEALTH, b'\x00'))
        result = self.transport.check_mcu_health()
        self.assertEqual(result, "Sain")
        self.assertTrue(self.transport._response_queue.empty())

    def test_check_mcu_health_timeout(self):
        """Test that check_mcu_health raises TimeoutError when no response."""
        # Ensure queue is empty
        self.assertTrue(self.transport._response_queue.empty())
        # We expect a timeout
        with self.assertRaises(TimeoutError):
            self.transport.check_mcu_health()

    def test_check_mcu_health_not_connected(self):
        """Test that check_mcu_health raises ConnectionError when not connected."""
        self.transport._state = ConnectionState.DISCONNECTED
        self.transport._serial = None
        with self.assertRaises(ConnectionError):
            self.transport.check_mcu_health()

    def test_enter_bootloader_not_connected(self):
        """Test that enter_bootloader raises ConnectionError when not connected."""
        self.transport._state = ConnectionState.DISCONNECTED
        self.transport._serial = None
        with self.assertRaises(ConnectionError):
            self.transport.enter_bootloader()


if __name__ == '__main__':
    unittest.main()