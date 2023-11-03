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
""" Parses the header define by the example given below. """
# Example C++ header
# // Michael Shafae
# // mshafae@csu.fullerton.edu
# // @mshafae
# // Partners: @kevinwortman

import itertools
import os.path
import re
from logger import setup_logger

header_keys = 'name email github partners'.split()

def null_dict_header():
    """Creates an empty dict header."""
    result_dict = {
        'name': '~Unknown_Name',
        'email': '~no-reply@csu.fullerton.edu',
        'github': '~Unknown_GitHub',
        'partners': '~Unknown_Partners',
    }
    return result_dict


def dict_header(file_path, silent=False, comments_startwith='//'):
    """Given a single string, parse the header and return the result
    as a dictionary with the keys class, email, github, asgt, comment.
    On parse error, log a descriptive message and return an empty dictionary."""
    
    assert(os.path.exists(file_path))
    with open(file_path, encoding='UTF-8') as file_handle:
        contents = file_handle.read()
    
    logger = setup_logger()
    file_name = os.path.basename(file_path)
    FAILURE = {}

    lines = contents.splitlines()

    # reject: empty source file
    if len(lines) == 0:
        if not silent:
            logger.warning('header missing because source file %s is empty', file_name)
        return FAILURE

    # reject: whitespace on first line
    assert len(lines) > 0
    if len(lines[0]) == 0 or lines[0].isspace():
        if not silent:
            logger.warning(
                f'%s: line 1: expected a {comments_startwith} comment holding '
                'a header, but found whitespace instead', file_name
            )
        return FAILURE

    # find prefix of all comment lines
    #
    # At this point we are permissive about leading and trailing whitespace, so
    # we can give constructive feedback about more important issues.
    # The strict whitespace check is last, below.
    comment_lines = list(
        itertools.takewhile(
            lambda line: line.lstrip().startswith(comments_startwith), lines
        )
    )

    if (
        len(comment_lines) > 0
        and comments_startwith == '#'
        and comment_lines[0].startswith('#!')
    ):
        # check for a shebang. If there, discard and continue
        comment_lines.pop(0)

    # reject: no comments (meaning the first line is neither whitespace nor a comment)
    if len(comment_lines) == 0:
        if not silent:
            logger.warning(
                '%s line 1: expected a %s comment holding '
                'a header, but instead found: %s', file_name, comments_startwith, {lines[0]}
            )
        return FAILURE

    # strip whitespace for parsing purposes
    header_lines = [line.strip() for line in comment_lines]

    # reject: header is impossibly short
    min_header_length = 4
    if len(header_lines) < min_header_length:
        if not silent:
            logger.warning(
                '%s: line %i: header is only %i lines long', file_name,
                len(header_lines) + 1,
                len(header_lines),
            )
            logger.warning(
                'a header must be at least %i lines long to contain all required information',
                min_header_length,
            )
        return FAILURE

    # reject: missing blank lines 6 or 9
    # def check_blank_line(line_number, previous_field_name):
    #     if header_lines[line_number - 1] != comments_startwith:
    #         if not silent:
    #             logger.warning(f'line {line_number}: should be a blank '
    #             f'{comments_startwith} comment after the {previous_field_name}')
    #         return False
    #     return True
    # if not check_blank_line(6, 'GitHub username'):
    #     return FAILURE
    # if comments_startwith == '//' and not check_blank_line(9, 'Partners'):
    #     return FAILURE

    # extract the fields: name, class, date, email, github, asgt, partners, comment
    # check that each is nonempty and has a space after //
    def check_field(line_number, name):
        line = header_lines[line_number - 1]
        assert line.startswith(comments_startwith)
        assert line.strip() == line
        if line == comments_startwith:
            if not silent:
                logger.warning(
                    '%s: line %i: should contain %s, but it is missing', file_name, line_number, name
                )
            return False
        assert len(line) > len(comments_startwith)
        if line[len(comments_startwith)] != ' ':
            if not silent:
                logger.warning(
                    '%s: line %i: there must be a space '
                    'between %s and %s', file_name, line_number, comments_startwith, name
                )
            return False
        assert len(line) > (
            len(comments_startwith) + 1
        )  # must be a non-whitespace char after '// '
        value = line[len(comments_startwith) :].strip()
        if len(value) == 0:
            if not silent:
                logger.warning('%s: line %i: %s field is empty', file_name, line_number, name)
            return False
        return value

    # NAME_LINE = 1
    # KLASS_LINE = 2
    # DATE_LINE = 3
    # EMAIL_LINE = 4
    # GITHUB_LINE = 5
    # ASSIGNMENT_LINE = 7
    # PARTNERS_LINE = 8
    # COMMENT_LINE = 10
    name_line = 1
    email_line = 2
    github_line = 3
    partners_line = 4
    # if comments_startwith == '#':
    #     COMMENT_LINE = 9

    name = check_field(name_line, 'name')
    # klass = check_field(KLASS_LINE, 'class') # class is a reserved word
    # date = check_field(DATE_LINE, 'date')
    email = check_field(email_line, 'email')
    github = check_field(github_line, 'GitHub')
    # assignment = check_field(ASSIGNMENT_LINE, 'assignment')
    if comments_startwith == '//':
        partners = check_field(partners_line, 'Partners:')
    else:
        partners = "None"
    # comment = check_field(COMMENT_LINE, 'comment')
    # if not all([name, klass, date, email, github, assignment, partners, comment]):
    #     return FAILURE

    if not all([name, email, github, partners]):
        return FAILURE

    # check name
    if not any([char.isalpha() for char in name]):
        if not silent:
            logger.warning('%s: line %i: does not resemble a name', file_name, name_line)
            logger.warning('a name is expected to have at least one letter')
        return FAILURE

    # check class
    # if not re.fullmatch('(?i)CPSC\s\d{3}[A-Z]?-\d{1,2}', klass):
    #     if not silent:
    #         logger.warning('line %i: does not resemble a class section number', KLASS_LINE)
    #         logger.warning('an example valid class section number is: 120L-01')
    #     return FAILURE

    # check date
    # try:
    #     datetime.date.fromisoformat(date)
    # except ValueError:
    #     if not silent:
    #         logger.warning('line %i: does not resemble a date in YYYY-MM-DD format', DATE_LINE)
    #         logger.warning('an example valid date is: 2022-12-31')
    #     return FAILURE

    # check email
    # any domain whatsoever
    if not re.fullmatch(r'\w+[.\-_0-9\w]*@.+', email):
        if not silent:
            logger.warning(
                '%s: line %i: does not resemble an email address', file_name, email_line
            )
            logger.warning(
                'an example email address is: adalovelace@csu.fullerton.edu'
            )
        return FAILURE
    # CSUF domain
    if not re.fullmatch(r'(?i)\w+[.\-_0-9\w]*@(csu\.)?fullerton\.edu', email):
        if not silent:
            logger.warning(
                '%s: line %i: email address is not CSUF-issued', file_name, email_line
            )
            logger.warning(
                'use your CSUF-issued email ending in @csu.fullerton.edu or @fullerton.edu'
            )
            logger.warning(
                'an example email address is: adalovelace@csu.fullerton.edu'
            )
        return FAILURE

    # github
    def is_github_username(github_login):  # will reuse this for partners below
        return bool(
            re.fullmatch(
                r'@([a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,38})',
                github_login,
            )
        )

    if not is_github_username(github):
        if not silent:
            logger.warning(
                '%s: line %i: does not resemble a GitHub username starting with @', file_name,
                github_line,
            )
            logger.warning('an example GitHub username is: @AdaLovelace')
            logger.warning(
                'leave the space blank if you do not have a partner.'
            )
        return FAILURE

    # assignment
    # if not re.fullmatch('(?i)Lab \d\d-\d\d', assignment):
    #     if not silent:
    #         logger.warning('line %i: does not resemble a Lab assignment number', ASSIGNMENT_LINE)
    #         logger.warning('an example lab assignment number is: Lab 01-02')
    #     return FAILURE

    # partners
    if comments_startwith == '//' and not partners.startswith('Partners:'):
        if not silent:
            logger.warning(
                '%s, line %i: does not contain a Partners: list', file_name, partners_line
            )
        return FAILURE
    if comments_startwith == '#':
        partner_string = 'None'
    else:
        partner_string = partners.split('Partners:')[1].strip()
        partner_usernames = [
            str.strip()
            for str in partner_string.split(',')
            if len(str.strip()) > 0
        ]
        partner_count = len(partner_usernames)
        if partner_count == 0:
            if not silent:
                logger.warning(
                    '%s: line %i: partners list is empty; expected you to have a '
                    'pair-programming partner',
                    file_name, partners_line,
                )
            # do not return FAILURE; proceed with grading this; life happens
        if partner_count > 2:
            if not silent:
                logger.warning(
                    '%s: line %i: expected only one or two partners, but you have %i', file_name,
                    partners_line,
                    partner_count,
                )
            # do not return FAILURE; proceed with grading this; life happens
        for username in partner_usernames:
            if not is_github_username(username):
                if not silent:
                    logger.warning(
                        '%s: line %i: partner "%s" does not resemble a GitHub username starting with @', file_name,
                        partners_line,
                        username,
                    )
                    logger.warning(
                        'an example GitHub username is: @AdaLovelace'
                    )
                    logger.warning(
                        'leave the space blank if you do not have a partner.'
                    )
                return FAILURE

    # comment
    # if not any([char.isalpha() for char in comment]):
    #     if not silent:
    #         logger.warning('line %i: does not resemble a descriptive comment', COMMENT_LINE)
    #         logger.warning('a descriptive comment is expected to have at '\
    #         least one letter', COMMENT_LINE)
    #     return FAILURE

    # finally check for stray whitespace
    # use the un-stripped source lines in comment_lines, not the stripped ones in header_lines
    for index, line in enumerate(comment_lines):
        if line != line.lstrip():
            if not silent:
                logger.warning(
                    '%s: line %i: unexpected leading whitespace; '
                    'delete whitespace before %s',
                    file_name, index + 1,
                    comments_startwith,
                )
            return FAILURE

    # Success!
    # create a dictionary object
    result_dict = {
        'name': name,
        'email': email,
        'github': github,
        'partners': partner_string,
    }

    return result_dict


# def parse_header(contents, keyword=None):
#     """Given Given a single string, parse the header and return the keyword's value."""
#     result = dict_header(contents)
#     if len(result) == 0:
#         return None  # failure
#     if keyword is None:
#         return result  # everything
#     if keyword in result:
#         return result[keyword]  # found single keyword
#     return None  # invalid keyword
