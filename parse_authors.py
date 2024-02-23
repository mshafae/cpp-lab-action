#
# Copyright 2021-2023 Michael Shafae
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
""" Parses the AUTHORS.md file. """

import itertools
import os.path
import re
from logger import setup_logger

header_keys = 'name email github'.split()

def null_authors_list():
    """Creates an empty authors list."""
    result_dict = {
        'name': '~Unknown_Name',
        'email': '~no-reply@csu.fullerton.edu',
        'github': '~Unknown_GitHub',
        'partners': '~Unknown_Partners',
    }
    return [result_dict]


def dict_authors(file_path):
    assert(os.path.exists(file_path))
    with open(file_path, encoding='UTF-8') as file_handle:
        contents = file_handle.read()
    logger = setup_logger()
    file_name = os.path.basename(file_path)
    # Strip out blank lines
    lines = list(filter(None, contents.splitlines()))
    authors = []
    FAILURE = []
    if len(lines) == 0:
        logger.error('Authors missing because source file %s is empty', file_name)
        return FAILURE

    author_lines = [line.strip() for line in lines]
    # reject: header is impossibly short
    min_author_length = 3
    if len(author_lines) < min_author_length:
        logger.error(
            '%s: file is only %i lines long; too few lines.', file_name,
            len(author_lines)
        )
        logger.error(
            'an AUTHORS.md file must be at least %i lines long to contain all required information',
            min_author_length,
        )
        return FAILURE

    if len(author_lines) % 3 != 0:
        logger.error(
            '%s: has an odd number of lines, %d. Each partner needs 3 lines.', file_name, len(author_lines)
        )
        
    def check_field(line_number, name):
        line = author_lines[line_number]
        assert line.strip() == line
        value = line.strip()
        if len(value) == 0:
            logger.warning('%s: line %i: %s field is empty', file_name, line_number, name)
            return False
        return value

    def is_github_username(github_login):  # will reuse this for partners below
        return bool(
            re.fullmatch(
                r'@([a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,38})',
                github_login,
            )
        )
    
    name_line = 0
    email_line = 1
    github_line = 2
    for starting_line in range(0, len(author_lines), 3):
        nl = starting_line + name_line
        el = starting_line + email_line
        gl = starting_line + github_line
        name = check_field(nl, 'name')
        email = check_field(el, 'email')
        github = check_field(gl, 'GitHub')
        if not all([name, email, github]):
            return FAILURE
        if not any([char.isalpha() for char in name]):
            logger.error('%s: line %i: does not resemble a name "%s"', file_name, nl, name)
            logger.error('a name is expected to have at least one letter')
            return FAILURE
        # check email
        # any domain whatsoever
        if not re.fullmatch(r'\w+[.\-_0-9\w]*@.+', email):
            logger.error(
                '%s: line %i: does not resemble an email address "%s"', file_name, el, email
            )
            logger.error(
                'an example email address is: adalovelace@csu.fullerton.edu'
            )
            return FAILURE
        # CSUF domain
        if not re.fullmatch(r'(?i)\w+[.\-_0-9\w]*@(csu\.)?fullerton\.edu', email):
            logger.error(
                '%s: line %i: email address is not CSUF-issued "%s"', file_name, el, email
            )
            logger.error(
                'use your CSUF-issued email ending in @csu.fullerton.edu or @fullerton.edu'
            )
            logger.error(
                'an example email address is: adalovelace@csu.fullerton.edu'
            )
            return FAILURE

        # github
        if not is_github_username(github):
            logger.error(
                '%s: line %i: does not resemble a GitHub username starting with @ "%s"', file_name,
                gl, github
            )
            logger.error('an example GitHub username is: @AdaLovelace')
            logger.error(
                'leave the space blank if you do not have a partner.'
            )
            return FAILURE
        author_dict = {
            'name': name,
            'email': email,
            'github': github,
        }
        authors.append(author_dict)
    return authors
