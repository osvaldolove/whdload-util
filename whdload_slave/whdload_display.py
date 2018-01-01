from collections import OrderedDict


class KickstartDisplay(object):
    def __init__(self, kickstart):
        self.kickstart = kickstart


class WHDLoadDisplay(object):
    PROPERTY_FRIENDLY_NAMES = OrderedDict(
        [
            ("path", "Path"),
            ("file_name", "File Name"),
            ("name", "Name"),
            ("copy", "Copyright"),
            ("info", "Info"),
            ("modified_time", "Modified Time"),
            ("base_mem_size", "Base Memory Size"),
            ("flags", "Flags"),
            ("current_dir", "Current Directory"),
            ("dont_cache", "Don't Cache"),
            ("debug_key", "Debug Key"),
            ("exit_key", "Exit Key"),
            ("exp_mem", "Expansion Memory Size"),
            ("kickstarts", "Kickstarts"),
            ("kickstart_size", "Kickstart Size"),
            ("config", "Config"),
            ('hash', 'SHA1 Hash')
        ]
    )

    SIZE_PROPERTIES = [
        'base_mem_size',
        'exp_mem',
        'kickstart_size'
    ]

    def __init__(self, slave):
        self.slave = slave
        self.padding = self._get_longest_property_name()

    def _get_longest_property_name(self):
        longest_prop_name = 0
        for _, friendly_name in self.PROPERTY_FRIENDLY_NAMES.items():
            prop_name_length = len(friendly_name)
            if prop_name_length > longest_prop_name:
                longest_prop_name = prop_name_length
        return longest_prop_name

    def _format_multi_line_props(self, value):
        old_value = value
        value = ""

        if not isinstance(old_value, list):
            old_value = old_value.split('\n')

        for i, line in enumerate(old_value):
            if i == 0:
                value += line
                continue
            value += '\n'.ljust(self.padding + 3)
            value += line
        return value

    def display_properties(self):
        for key, friendly_name in self.PROPERTY_FRIENDLY_NAMES.items():
            # Pad friendly name to align columns
            friendly_name = friendly_name.ljust(self.padding)

            if hasattr(self.slave, key):
                value = getattr(self.slave, key)
                if not value:
                    continue

                # Display Memory Sizes in Friendly Format
                if key in self.SIZE_PROPERTIES:
                    value = "{} KiB ({})".format(value // 1024, hex(value))

                # Disply formatted info property
                if key == 'info':
                    value = self._format_multi_line_props(value)

                # Display formatted list properties
                if isinstance(value, list):
                    value = self._format_multi_line_props(value)

                # Display formatted Kickstart property
                if key == "kickstarts":
                    old_value = value
                    value = ""
                    for kickstart in old_value:
                        value += "\n\tName: {}\n\tCRC: {}".format(
                            kickstart.name, kickstart.crc)

                yield friendly_name, value
