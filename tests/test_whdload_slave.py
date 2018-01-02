#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `whdload_slave` package."""

import pytest

import os

from click.testing import CliRunner

from whdload_slave import whdload_slave
from whdload_slave import cli


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


@pytest.fixture
def flimbos_quest_slave():
    return os.path.join(
        os.path.dirname(__file__), 'data', 'FlimbosQuest.slave')


def test_whdload_slave(flimbos_quest_slave):
    runner = CliRunner()
    result = runner.invoke(cli.main, [flimbos_quest_slave])
    assert result.exit_code == 0
    assert "WHDLoad Slave Reader" in result.output
    assert "13d48741b7a374436c0c32ea95823067fe9dcda8" in result.output


# def test_command_line_interface():
#     """Test the CLI."""
#     runner = CliRunner()
#     result = runner.invoke(cli.main)
#     assert result.exit_code == 0
#     assert 'whdload_slave.cli.main' in result.output
#     help_result = runner.invoke(cli.main, ['--help'])
#     assert help_result.exit_code == 0
#     assert '--help  Show this message and exit.' in help_result.output
