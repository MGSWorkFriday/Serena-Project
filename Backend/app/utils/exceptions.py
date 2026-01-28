# -*- coding: utf-8 -*-
"""Custom exceptions"""
from __future__ import annotations


class SerenaException(Exception):
    """Base exception for Serena application"""
    pass


class DeviceNotFoundError(SerenaException):
    """Device not found"""
    pass


class SessionNotFoundError(SerenaException):
    """Session not found"""
    pass


class TechniqueNotFoundError(SerenaException):
    """Technique not found"""
    pass


class ParameterSetNotFoundError(SerenaException):
    """Parameter set not found"""
    pass
