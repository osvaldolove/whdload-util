# -*- coding: utf-8 -*-
"""Main module."""
import os
import struct
import binascii
import datetime
import re
import hashlib


class Kickstart(object):
    def __init__(self, name, crc):
        self.name = name
        self.crc = crc

    def __str__(self):
        return "{}: {}".format(self.name, self.crc)


class WHDLoadSlaveBase(object):
    HEADER_OFFSET = 0x020  # 32 bytes
    FLAGS = {
        1: 'Disk',
        2: 'NoError',
        4: 'EmulTrap',
        8: 'NoDivZero',
        16: 'Req68020',
        32: 'ReqAGA',
        64: 'NoKbd',
        128: 'EmulLineA',
        256: 'EmulTrapV',
        512: 'EmEmulChkul',
        1024: 'EmulPriv',
        2048: 'EmulLineF',
        4096: 'ClearMem',
        8192: 'Examine',
        16384: 'EmulDivZero',
        32768: 'EmulIllegal'
    }

    def __init__(self):
        self.path = None
        self.file_name = None
        self.modified_time = None
        self.size = None
        self.data_length = None
        self.security = None
        self.id = None
        self.version = None
        self.flags_value = None
        self.base_mem_size = None
        self.exec_install = None
        self.game_loader = None
        self.current_dir_offset = None
        self.dont_cache_offset = None
        self.key_debug = None
        self.key_exit = None
        self.exp_mem = 0
        self.name_offset = None
        self.copy_offset = None
        self.info_offset = None
        self.config_offset = None
        self.current_dir = None
        self.config = None
        self.dont_cache = None
        self.name = None
        self.copy = None
        self.info = None
        self.kickstarts = []
        self.kick_name_offset = None
        self.kickstart_size = 0
        self.flags = []
        self.read = None

    def requires_aga(self):
        return "ReqAGA" in self.flags

    def requires_68020(self):
        return "Req68020" in self.flags

    def has_cd32_controls_patch(self):
        if self.config is not None and len(self.config) > 0:
            for config_item in self.config:
                config_item_values = config_item.split(':')
                try:
                    if re.match("^.*[Cc][Dd]32.*$", config_item_values[2]):
                        return True
                except IndexError:
                    pass
        return False

    def compare_property(self, other_slave, property_name):
        try:
            this_property = getattr(self, property_name)
            other_slave_property = getattr(other_slave, property_name)
            if this_property == other_slave_property:
                return True
        except AttributeError:
            return False

        return False

    def compare_names(self, other_slave):
        return self.compare_property(other_slave, "name")

    def compare_file_names(self, other_slave):
        return self.compare_property(other_slave, "file_name")

    def compare_all(self, other_slave):
        compare_list = [
            self.compare_names,
            self.compare_file_names,
        ]

        compare = True
        for compare_func in compare_list:
            compare = compare_func(other_slave)
            if compare is False:
                break

        return compare


class WHDLoadSlaveFile(WHDLoadSlaveBase):
    def __init__(self, path):
        WHDLoadSlaveBase.__init__(self)
        self.path = path
        self.file_name = os.path.basename(path)
        self.modified_time = datetime.datetime.fromtimestamp(
            os.path.getmtime(path))
        self.hash = None
        self.read = self._path_read

    def read(self):
        raise NotImplementedError

    @staticmethod
    def _read_string(offset, data):
        if offset == 0:
            return ""
        length = 0
        for byte in data[offset:]:
            if byte == 0:
                break
            length += 1

        return struct.unpack_from('{}s'.format(length),
                                  data[offset:])[0].decode('iso-8859-1')

    @classmethod
    def from_file(cls, file):
        whd = cls(file.name)
        whd.read = whd._file_read
        whd.size = len(file.peek())
        whd.hash = hashlib.sha1(file.peek()).hexdigest()
        whd.data_length = whd.size - whd.HEADER_OFFSET
        return whd

    @classmethod
    def from_path(cls, path):
        whd = cls(path)
        whd.read = whd._path_read
        return whd

    def _file_read(self, file):
        file.seek(self.HEADER_OFFSET, 0)
        _data = bytearray(file.read())
        file.close()
        self._parse_data(_data)
        self._parse_flags(_data)

    def _path_read(self):
        self._get_file_size()

        with open(self.path, 'rb') as f:
            self.hash = hashlib.sha1(f.read()).hexdigest()
            f.seek(self.HEADER_OFFSET, 0)
            _data = bytearray(f.read())

        self._parse_data(_data)
        self._parse_flags()

    def _get_file_size(self):
        self.size = os.path.getsize(self.path)
        self.data_length = self.size - self.HEADER_OFFSET

    def _parse_data(self, data):
        self.security = struct.unpack_from('>L', data[0:])[0]
        self.id = struct.unpack_from('8s', data[4:])[0].decode('iso-8859-1')
        self.version = struct.unpack_from('>H', data[12:])[0]
        self.flags_value = struct.unpack_from('>H', data[14:])[0]
        self.base_mem_size = struct.unpack_from('>L', data[16:])[0]
        self.exec_install = struct.unpack_from('>L', data[20:])[0]
        self.game_loader = struct.unpack_from('>H', data[24:])[0]
        self.current_dir_offset = struct.unpack_from('>H', data[26:])[0]
        self.dont_cache_offset = struct.unpack_from('>H', data[28:])[0]

        _kickstart_crc = 0

        if self.version >= 4:
            self.key_debug = binascii.hexlify(
                struct.unpack_from('c', data[30:])[0]).decode('iso-8859-1')
            self.key_exit = binascii.hexlify(
                struct.unpack_from('c', data[31:])[0]).decode('iso-8859-1')

        if self.version >= 8:
            self.exp_mem = struct.unpack_from('>L', data[32:])[0]

        if self.version >= 10:
            self.name_offset = struct.unpack_from('>H', data[36:])[0]
            self.copy_offset = struct.unpack_from('>H', data[38:])[0]
            self.info_offset = struct.unpack_from('>H', data[40:])[0]

        if self.version >= 16:
            self.kick_name_offset = struct.unpack_from('>H', data[42:])[0]
            self.kickstart_size = struct.unpack_from('>L', data[44:])[0]
            _kickstart_crc = struct.unpack_from('>H', data[48:])[0]

        if self.version >= 17:
            self.config_offset = struct.unpack_from('>H', data[50:])[0]

        if self.id != "WHDLOADS":
            raise Exception(
                "Failed to read header: Id is not valid '{}'".format(self.id))

        self.current_dir = self._read_string(self.current_dir_offset, data)
        self.dont_cache = self._read_string(self.dont_cache_offset, data)

        if self.version >= 10:
            self.name = self._read_string(self.name_offset, data)
            self.copy = self._read_string(self.copy_offset, data)
            _info = self._read_string(self.info_offset, data)
            self.info = "\n".join(([x for x in _info.split('\n') if x != ""]))

        if self.version >= 16:
            # The crc flag is set to indicate that there a multiple supported kickstarts
            if _kickstart_crc == 65535:
                self._parse_multiple_kickstarts(self.kick_name_offset, data)
            elif _kickstart_crc != 0:
                self.kickstarts.append(
                    Kickstart(
                        name=self._read_string(self.kick_name_offset, data),
                        crc=hex(_kickstart_crc)))

        if self.version >= 17:
            self.config = self._read_string(self.config_offset,
                                            data).split(';')

    def _parse_multiple_kickstarts(self, offset, data):
        offset_counter = offset
        while True:
            kick_crc = struct.unpack_from('>H', data[offset_counter:])[0]
            if kick_crc == 0:
                break
            offset_counter += 2
            kick_name = self._read_string(
                struct.unpack_from('>H', data[offset_counter:])[0], data)
            offset_counter += 2
            self.kickstarts.append(
                Kickstart(name=kick_name, crc=hex(kick_crc)))

    def _parse_flags(self):
        for key, value in self.FLAGS.items():
            if self.flags_value & key:
                self.flags.append(value)
